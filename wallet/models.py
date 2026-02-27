"""
Wallet model for managing user balances
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Wallet(models.Model):
    """
    Wallet model with OneToOne relationship to User
    Stores user's balance with proper decimal handling for money
    """
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OneToOne relationship with User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Balance field - using DecimalField for precise money calculations
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Wallet for {self.user.email} - Balance: {self.balance}"
    
    def can_debit(self, amount):
        """Check if wallet has sufficient balance for debit"""
        return self.balance >= amount
    
    def credit(self, amount):
        """Add money to wallet"""
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        
        self.balance += Decimal(str(amount))
        self.save(update_fields=['balance', 'updated_at'])
        return self.balance
    
    def debit(self, amount):
        """Deduct money from wallet"""
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        
        if not self.can_debit(amount):
            from fintech_core.exceptions import InsufficientBalanceError
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: {self.balance}, Required: {amount}"
            )
        
        self.balance -= Decimal(str(amount))
        self.save(update_fields=['balance', 'updated_at'])
        return self.balance
