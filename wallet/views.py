"""
Views for wallet management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import logging

from .models import Wallet
from .serializers import WalletSerializer, WalletBalanceSerializer

logger = logging.getLogger('wallet')


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for wallet management
    Provides read-only access to wallet information
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return wallet for current user only"""
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current wallet balance"""
        wallet = request.user.wallet
        serializer = WalletBalanceSerializer({
            'balance': wallet.balance,
            'currency': 'USD'
        })
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def info(self, request):
        """Get detailed wallet information"""
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)
