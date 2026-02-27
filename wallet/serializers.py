"""
Serializers for wallet
"""
from rest_framework import serializers
from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id',
            'user_email',
            'user_name',
            'balance',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']


class WalletBalanceSerializer(serializers.Serializer):
    """Serializer for wallet balance display"""
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    currency = serializers.CharField(default='USD', read_only=True)
