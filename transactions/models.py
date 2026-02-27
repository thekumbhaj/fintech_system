"""
Transaction model for ledger and transfers
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Transaction(models.Model):
    """
    Transaction model for tracking all money movements
    Implements double-entry accounting principles
    """
    
    class TransactionType(models.TextChoices):
        TRANSFER = 'TRANSFER', 'Transfer'
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        REFUND = 'REFUND', 'Refund'
        FEE = 'FEE', 'Fee'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Unique reference ID for idempotency
    reference_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique reference ID for idempotency"
    )
    
    # Transaction participants
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions_sent',
        null=True,
        blank=True,
        help_text="User sending money (null for deposits)"
    )
    
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions_received',
        null=True,
        blank=True,
        help_text="User receiving money (null for withdrawals)"
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True
    )
    
    # Description and metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Balances after transaction (for audit trail)
    from_balance_before = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    from_balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    to_balance_before = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    to_balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_id']),
            models.Index(fields=['from_user', 'created_at']),
            models.Index(fields=['to_user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.reference_id} - {self.amount}"
    
    def mark_completed(self):
        """Mark transaction as completed"""
        from django.utils import timezone
        self.status = self.TransactionStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark transaction as failed"""
        self.status = self.TransactionStatus.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])


class TransactionLedger(models.Model):
    """
    Ledger entries for double-entry accounting
    Each transaction creates two ledger entries (debit and credit)
    """
    
    class EntryType(models.TextChoices):
        DEBIT = 'DEBIT', 'Debit'
        CREDIT = 'CREDIT', 'Credit'
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to transaction
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    
    # User and wallet involved
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    
    # Entry details
    entry_type = models.CharField(
        max_length=10,
        choices=EntryType.choices,
        db_index=True
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'transaction_ledger'
        verbose_name = 'Transaction Ledger Entry'
        verbose_name_plural = 'Transaction Ledger Entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction']),
            models.Index(fields=['entry_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.entry_type} - {self.user.email} - {self.amount}"
