"""
Payment models for tracking payment gateway transactions
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class PaymentIntent(models.Model):
    """
    Payment Intent model for tracking payment gateway transactions
    Similar to Stripe's PaymentIntent or Razorpay's Order
    """
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        SUCCEEDED = 'SUCCEEDED', 'Succeeded'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class PaymentMethod(models.TextChoices):
        CARD = 'CARD', 'Credit/Debit Card'
        UPI = 'UPI', 'UPI'
        NET_BANKING = 'NET_BANKING', 'Net Banking'
        WALLET = 'WALLET', 'Wallet'
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Payment gateway reference
    gateway_payment_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Payment ID from payment gateway"
    )
    
    # User making payment
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payment_intents'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField(max_length=3, default='USD')
    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # Description and metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Gateway response
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    succeeded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_intents'
        verbose_name = 'Payment Intent'
        verbose_name_plural = 'Payment Intents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gateway_payment_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.gateway_payment_id} - {self.amount} {self.currency}"
    
    def mark_succeeded(self):
        """Mark payment as succeeded"""
        from django.utils import timezone
        self.status = self.PaymentStatus.SUCCEEDED
        self.succeeded_at = timezone.now()
        self.save(update_fields=['status', 'succeeded_at', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark payment as failed"""
        self.status = self.PaymentStatus.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])


class WebhookEvent(models.Model):
    """
    Model for tracking webhook events from payment gateway
    """
    
    class EventStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        PROCESSED = 'PROCESSED', 'Processed'
        FAILED = 'FAILED', 'Failed'
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event details
    event_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique event ID from gateway"
    )
    
    event_type = models.CharField(max_length=100, db_index=True)
    
    # Payload
    payload = models.JSONField()
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.PENDING,
        db_index=True
    )
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_events'
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.event_id} - {self.event_type}"
    
    def mark_processed(self):
        """Mark webhook as processed"""
        from django.utils import timezone
        self.status = self.EventStatus.PROCESSED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_failed(self, error_message):
        """Mark webhook as failed"""
        self.status = self.EventStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count'])
