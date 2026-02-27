"""
Serializers for payments
"""
from rest_framework import serializers
from .models import PaymentIntent, WebhookEvent


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for Payment Intent"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id',
            'gateway_payment_id',
            'user_email',
            'amount',
            'currency',
            'payment_method',
            'status',
            'description',
            'metadata',
            'error_message',
            'created_at',
            'succeeded_at',
        ]
        read_only_fields = [
            'id',
            'gateway_payment_id',
            'status',
            'error_message',
            'created_at',
            'succeeded_at',
        ]


class CreatePaymentIntentSerializer(serializers.Serializer):
    """Serializer for creating payment intent"""
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        required=True
    )
    currency = serializers.CharField(default='USD', max_length=3)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_amount(self, value):
        """Validate payment amount"""
        from django.conf import settings
        
        if value < settings.MIN_TRANSACTION_AMOUNT:
            raise serializers.ValidationError(
                f"Amount must be at least {settings.MIN_TRANSACTION_AMOUNT}"
            )
        
        if value > settings.MAX_TRANSACTION_AMOUNT:
            raise serializers.ValidationError(
                f"Amount cannot exceed {settings.MAX_TRANSACTION_AMOUNT}"
            )
        
        return value


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for Webhook Event"""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id',
            'event_id',
            'event_type',
            'status',
            'error_message',
            'retry_count',
            'created_at',
            'processed_at',
        ]
        read_only_fields = '__all__'
