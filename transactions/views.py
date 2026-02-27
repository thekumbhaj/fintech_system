"""
Views for transaction management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging

from .models import Transaction, TransactionLedger
from .serializers import (
    TransactionSerializer,
    TransferRequestSerializer,
    LedgerEntrySerializer,
    TransactionHistorySerializer,
)
from .services import TransactionService
from users.models import User
from fintech_core.exceptions import (
    InsufficientBalanceError,
    InvalidTransactionError,
    DuplicateTransactionError,
)

logger = logging.getLogger('transactions')


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for transaction management
    Provides read access to transactions and transfer action
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'transaction_type']
    ordering_fields = ['created_at', 'amount']
    search_fields = ['reference_id', 'description']
    
    def get_queryset(self):
        """Return transactions for current user"""
        user = self.request.user
        return Transaction.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).select_related('from_user', 'to_user')
    
    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'])
    def transfer(self, request):
        """
        Transfer money to another user
        Implements rate limiting to prevent abuse
        """
        serializer = TransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from_user = request.user
        to_user_email = serializer.validated_data['to_user_email']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        idempotency_key = serializer.validated_data.get('idempotency_key')
        
        # Get recipient user
        try:
            to_user = User.objects.get(email=to_user_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Recipient user not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Perform transfer
        try:
            transaction = TransactionService.transfer_money(
                from_user=from_user,
                to_user=to_user,
                amount=amount,
                description=description,
                idempotency_key=idempotency_key,
            )
            
            return Response(
                {
                    'message': 'Transfer completed successfully',
                    'transaction': TransactionSerializer(transaction).data
                },
                status=status.HTTP_201_CREATED
            )
            
        except InsufficientBalanceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except InvalidTransactionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Transfer failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Transfer failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get transaction history with direction (sent/received)
        """
        user = request.user
        transactions = self.get_queryset()
        
        history_data = []
        for txn in transactions:
            # Determine direction and other party
            if txn.from_user == user:
                direction = 'sent'
                other_party_email = txn.to_user.email if txn.to_user else None
                balance_after = txn.from_balance_after
            elif txn.to_user == user:
                direction = 'received'
                other_party_email = txn.from_user.email if txn.from_user else None
                balance_after = txn.to_balance_after
            else:
                continue
            
            history_data.append({
                'id': txn.id,
                'reference_id': txn.reference_id,
                'amount': txn.amount,
                'transaction_type': txn.transaction_type,
                'status': txn.status,
                'description': txn.description,
                'direction': direction,
                'other_party_email': other_party_email,
                'balance_after': balance_after,
                'created_at': txn.created_at,
                'completed_at': txn.completed_at,
            })
        
        serializer = TransactionHistorySerializer(history_data, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        """Get ledger entries for a transaction"""
        transaction = self.get_object()
        ledger_entries = transaction.ledger_entries.all()
        serializer = LedgerEntrySerializer(ledger_entries, many=True)
        return Response(serializer.data)


class LedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ledger entries
    Provides read-only access to user's ledger entries
    """
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        """Return ledger entries for current user"""
        return TransactionLedger.objects.filter(
            user=self.request.user
        ).select_related('transaction', 'user')
