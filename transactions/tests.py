"""
Tests for transactions service
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from users.models import User
from wallet.models import Wallet
from transactions.models import Transaction, TransactionLedger
from transactions.services import TransactionService
from fintech_core.exceptions import InsufficientBalanceError, InvalidTransactionError

User = get_user_model()


@pytest.mark.django_db
class TestTransactionService:
    """Test suite for TransactionService"""
    
    @pytest.fixture
    def user1(self):
        """Create test user 1"""
        user = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
        )
        user.kyc_status = User.KYCStatus.VERIFIED
        user.save()
        return user
    
    @pytest.fixture
    def user2(self):
        """Create test user 2"""
        user = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
        )
        user.kyc_status = User.KYCStatus.VERIFIED
        user.save()
        return user
    
    def test_wallet_auto_created(self, user1):
        """Test that wallet is automatically created for user"""
        assert hasattr(user1, 'wallet')
        assert user1.wallet.balance == Decimal('0.00')
    
    def test_add_money_success(self, user1):
        """Test adding money to wallet"""
        initial_balance = user1.wallet.balance
        amount = Decimal('100.00')
        
        txn = TransactionService.add_money(
            user=user1,
            amount=amount,
            description='Test deposit'
        )
        
        # Refresh wallet
        user1.wallet.refresh_from_db()
        
        # Assertions
        assert txn.status == Transaction.TransactionStatus.COMPLETED
        assert txn.amount == amount
        assert txn.transaction_type == Transaction.TransactionType.DEPOSIT
        assert user1.wallet.balance == initial_balance + amount
        
        # Check ledger entry
        ledger_entries = TransactionLedger.objects.filter(transaction=txn)
        assert ledger_entries.count() == 1
        assert ledger_entries.first().entry_type == TransactionLedger.EntryType.CREDIT
    
    def test_transfer_success(self, user1, user2):
        """Test successful money transfer"""
        # Add money to user1
        TransactionService.add_money(user1, Decimal('200.00'))
        
        user1.wallet.refresh_from_db()
        user2.wallet.refresh_from_db()
        
        initial_balance1 = user1.wallet.balance
        initial_balance2 = user2.wallet.balance
        transfer_amount = Decimal('50.00')
        
        # Transfer money
        txn = TransactionService.transfer_money(
            from_user=user1,
            to_user=user2,
            amount=transfer_amount,
            description='Test transfer'
        )
        
        # Refresh wallets
        user1.wallet.refresh_from_db()
        user2.wallet.refresh_from_db()
        
        # Assertions
        assert txn.status == Transaction.TransactionStatus.COMPLETED
        assert txn.amount == transfer_amount
        assert txn.transaction_type == Transaction.TransactionType.TRANSFER
        assert user1.wallet.balance == initial_balance1 - transfer_amount
        assert user2.wallet.balance == initial_balance2 + transfer_amount
        
        # Check ledger entries
        ledger_entries = TransactionLedger.objects.filter(transaction=txn)
        assert ledger_entries.count() == 2
        
        debit_entry = ledger_entries.filter(entry_type=TransactionLedger.EntryType.DEBIT).first()
        credit_entry = ledger_entries.filter(entry_type=TransactionLedger.EntryType.CREDIT).first()
        
        assert debit_entry.user == user1
        assert credit_entry.user == user2
        assert debit_entry.amount == transfer_amount
        assert credit_entry.amount == transfer_amount
    
    def test_transfer_insufficient_balance(self, user1, user2):
        """Test transfer with insufficient balance"""
        transfer_amount = Decimal('100.00')
        
        with pytest.raises(InsufficientBalanceError):
            TransactionService.transfer_money(
                from_user=user1,
                to_user=user2,
                amount=transfer_amount,
                description='Test transfer'
            )
    
    def test_transfer_to_self(self, user1):
        """Test that transfer to self is not allowed"""
        TransactionService.add_money(user1, Decimal('100.00'))
        
        with pytest.raises(InvalidTransactionError):
            TransactionService.transfer_money(
                from_user=user1,
                to_user=user1,
                amount=Decimal('50.00'),
                description='Self transfer'
            )
    
    def test_transfer_unverified_user(self, user1, user2):
        """Test that unverified users cannot transact"""
        # Add money to user1
        TransactionService.add_money(user1, Decimal('100.00'))
        
        # Set user2 as unverified
        user2.kyc_status = User.KYCStatus.PENDING
        user2.save()
        
        with pytest.raises(InvalidTransactionError):
            TransactionService.transfer_money(
                from_user=user1,
                to_user=user2,
                amount=Decimal('50.00'),
                description='Transfer to unverified'
            )
    
    def test_idempotency(self, user1, user2):
        """Test transaction idempotency"""
        # Add money to user1
        TransactionService.add_money(user1, Decimal('200.00'))
        
        idempotency_key = 'TEST-IDEMPOTENT-KEY'
        
        # First transfer
        txn1 = TransactionService.transfer_money(
            from_user=user1,
            to_user=user2,
            amount=Decimal('50.00'),
            idempotency_key=idempotency_key
        )
        
        user1.wallet.refresh_from_db()
        balance_after_first = user1.wallet.balance
        
        # Second transfer with same key (should return same transaction)
        txn2 = TransactionService.transfer_money(
            from_user=user1,
            to_user=user2,
            amount=Decimal('50.00'),
            idempotency_key=idempotency_key
        )
        
        user1.wallet.refresh_from_db()
        
        # Assertions
        assert txn1.id == txn2.id
        assert user1.wallet.balance == balance_after_first  # Balance unchanged
