"""
Serializers for transactions
"""
from rest_framework import serializers
from .models import Transaction, TransactionLedger


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    from_user_email = serializers.EmailField(source='from_user.email', read_only=True)
    to_user_email = serializers.EmailField(source='to_user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference_id',
            'from_user_email',
            'to_user_email',
            'amount',
            'transaction_type',
            'status',
            'description',
            'metadata',
            'from_balance_before',
            'from_balance_after',
            'to_balance_before',
            'to_balance_after',
            'error_message',
            'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'reference_id',
            'status',
            'from_balance_before',
            'from_balance_after',
            'to_balance_before',
            'to_balance_after',
            'error_message',
            'created_at',
            'completed_at',
        ]


class TransferRequestSerializer(serializers.Serializer):
    """Serializer for transfer request"""
    to_user_email = serializers.EmailField(required=True)
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        required=True
    )
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=100)
    
    def validate_amount(self, value):
        """Validate transaction amount"""
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
    
    def validate_to_user_email(self, value):
        """Validate recipient email"""
        from users.models import User
        
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("Recipient account is not active")
            if not user.can_transact():
                raise serializers.ValidationError("Recipient is not verified to receive transactions")
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient user does not exist")
        
        return value


class LedgerEntrySerializer(serializers.ModelSerializer):
    """Serializer for Ledger Entry"""
    transaction_reference = serializers.CharField(source='transaction.reference_id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = TransactionLedger
        fields = [
            'id',
            'transaction_reference',
            'user_email',
            'entry_type',
            'amount',
            'balance_after',
            'created_at',
        ]
        read_only_fields = '__all__'


class TransactionHistorySerializer(serializers.Serializer):
    """Serializer for transaction history with direction"""
    id = serializers.UUIDField()
    reference_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField()
    direction = serializers.CharField()  # 'sent', 'received', 'self'
    other_party_email = serializers.EmailField(allow_null=True)
    balance_after = serializers.DecimalField(max_digits=15, decimal_places=2)
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)
