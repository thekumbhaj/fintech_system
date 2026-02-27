"""
Service layer for transaction processing
Handles atomic operations and row locking
"""
from django.db import transaction, IntegrityError
from django.core.cache import cache
from django.conf import settings
from decimal import Decimal
import logging
import uuid

from wallet.models import Wallet
from .models import Transaction, TransactionLedger
from fintech_core.exceptions import (
    InsufficientBalanceError,
    InvalidTransactionError,
    DuplicateTransactionError,
)

logger = logging.getLogger('transactions')


class TransactionService:
    """Service class for handling financial transactions"""
    
    @staticmethod
    def generate_reference_id():
        """Generate unique reference ID"""
        return f"TXN-{uuid.uuid4().hex.upper()[:16]}"
    
    @staticmethod
    def check_idempotency(idempotency_key):
        """Check if transaction with idempotency key already exists"""
        if not idempotency_key:
            return None
        
        # Check cache first
        cache_key = f"txn_idempotency:{idempotency_key}"
        cached_txn_id = cache.get(cache_key)
        
        if cached_txn_id:
            try:
                return Transaction.objects.get(id=cached_txn_id)
            except Transaction.DoesNotExist:
                cache.delete(cache_key)
        
        # Check database
        try:
            txn = Transaction.objects.get(reference_id=idempotency_key)
            cache.set(cache_key, str(txn.id), settings.TRANSACTION_IDEMPOTENCY_TIMEOUT)
            return txn
        except Transaction.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def transfer_money(from_user, to_user, amount, description='', idempotency_key=None):
        """
        Transfer money between users with atomic transaction and row locking
        Implements idempotency and proper error handling
        """
        amount = Decimal(str(amount))
        
        # Validation
        if from_user == to_user:
            raise InvalidTransactionError("Cannot transfer to yourself")
        
        if not from_user.can_transact():
            raise InvalidTransactionError("Sender is not verified to perform transactions")
        
        if not to_user.can_transact():
            raise InvalidTransactionError("Recipient is not verified to receive transactions")
        
        # Check idempotency
        reference_id = idempotency_key if idempotency_key else TransactionService.generate_reference_id()
        
        existing_txn = TransactionService.check_idempotency(reference_id)
        if existing_txn:
            logger.info(f"Duplicate transaction detected: {reference_id}")
            return existing_txn
        
        # Create transaction record (handle potential race on reference_id)
        try:
            txn = Transaction.objects.create(
                reference_id=reference_id,
                from_user=from_user,
                to_user=to_user,
                amount=amount,
                transaction_type=Transaction.TransactionType.TRANSFER,
                status=Transaction.TransactionStatus.PROCESSING,
                description=description,
            )
        except IntegrityError:
            existing = TransactionService.check_idempotency(reference_id)
            if existing:
                return existing
            raise
        
        try:
            # Lock wallets for update (prevent race conditions)
            from_wallet = Wallet.objects.select_for_update().get(user=from_user)
            to_wallet = Wallet.objects.select_for_update().get(user=to_user)
            
            # Record balances before
            txn.from_balance_before = from_wallet.balance
            txn.to_balance_before = to_wallet.balance
            
            # Check sufficient balance
            if not from_wallet.can_debit(amount):
                raise InsufficientBalanceError(
                    f"Insufficient balance. Available: {from_wallet.balance}, Required: {amount}"
                )
            
            # Perform transfer
            from_wallet.debit(amount)
            to_wallet.credit(amount)
            
            # Record balances after
            txn.from_balance_after = from_wallet.balance
            txn.to_balance_after = to_wallet.balance
            
            # Create ledger entries
            TransactionLedger.objects.create(
                transaction=txn,
                user=from_user,
                entry_type=TransactionLedger.EntryType.DEBIT,
                amount=amount,
                balance_after=from_wallet.balance,
            )
            
            TransactionLedger.objects.create(
                transaction=txn,
                user=to_user,
                entry_type=TransactionLedger.EntryType.CREDIT,
                amount=amount,
                balance_after=to_wallet.balance,
            )
            
            # Mark transaction as completed
            txn.mark_completed()
            
            # Cache the transaction ID for idempotency
            if reference_id:
                cache_key = f"txn_idempotency:{reference_id}"
                cache.set(cache_key, str(txn.id), settings.TRANSACTION_IDEMPOTENCY_TIMEOUT)
            
            logger.info(
                f"Transfer completed: {txn.reference_id} | "
                f"From: {from_user.email} | To: {to_user.email} | Amount: {amount}"
            )
            
            return txn
            
        except InsufficientBalanceError as e:
            txn.mark_failed(str(e))
            logger.warning(f"Transfer failed - insufficient balance: {txn.reference_id}")
            raise
            
        except Exception as e:
            txn.mark_failed(str(e))
            logger.error(f"Transfer failed: {txn.reference_id} - {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    @transaction.atomic
    def add_money(user, amount, description='', reference_id=None):
        """
        Add money to user wallet (deposit)
        Used by payment gateway webhooks
        """
        amount = Decimal(str(amount))
        
        if not reference_id:
            reference_id = TransactionService.generate_reference_id()
        
        # Check idempotency
        existing_txn = TransactionService.check_idempotency(reference_id)
        if existing_txn:
            logger.info(f"Duplicate deposit detected: {reference_id}")
            return existing_txn
        
        # Create transaction record (handle potential race on reference_id)
        try:
            txn = Transaction.objects.create(
                reference_id=reference_id,
                to_user=user,
                amount=amount,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                status=Transaction.TransactionStatus.PROCESSING,
                description=description,
            )
        except IntegrityError:
            existing = TransactionService.check_idempotency(reference_id)
            if existing:
                return existing
            raise
        
        try:
            # Lock wallet for update
            wallet = Wallet.objects.select_for_update().get(user=user)
            
            # Record balance before
            txn.to_balance_before = wallet.balance
            
            # Add money
            wallet.credit(amount)
            
            # Record balance after
            txn.to_balance_after = wallet.balance
            
            # Create ledger entry
            TransactionLedger.objects.create(
                transaction=txn,
                user=user,
                entry_type=TransactionLedger.EntryType.CREDIT,
                amount=amount,
                balance_after=wallet.balance,
            )
            
            # Mark transaction as completed
            txn.mark_completed()
            
            # Cache the transaction ID for idempotency
            cache_key = f"txn_idempotency:{reference_id}"
            cache.set(cache_key, str(txn.id), settings.TRANSACTION_IDEMPOTENCY_TIMEOUT)
            
            logger.info(
                f"Deposit completed: {txn.reference_id} | "
                f"User: {user.email} | Amount: {amount}"
            )
            
            return txn
            
        except Exception as e:
            txn.mark_failed(str(e))
            logger.error(f"Deposit failed: {txn.reference_id} - {str(e)}", exc_info=True)
            raise
