"""
Views for payment management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import logging
import json

from .models import PaymentIntent, WebhookEvent
from .serializers import (
    PaymentIntentSerializer,
    CreatePaymentIntentSerializer,
    WebhookEventSerializer,
)
from .services import PaymentService
from .tasks import process_webhook_async

logger = logging.getLogger('payments')


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for payment management
    """
    serializer_class = PaymentIntentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        """Return payments for current user"""
        return PaymentIntent.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_intent(self, request):
        """
        Create a payment intent to add money to wallet
        """
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        currency = serializer.validated_data.get('currency', 'USD')
        description = serializer.validated_data.get('description', 'Add money to wallet')
        
        try:
            payment_intent = PaymentService.create_payment_intent(
                user=request.user,
                amount=amount,
                currency=currency,
                description=description,
            )
            
            return Response(
                {
                    'message': 'Payment intent created successfully',
                    'payment_intent': PaymentIntentSerializer(payment_intent).data,
                    # In production, return payment gateway URL or client_secret
                    'payment_url': f'/api/payments/simulate/{payment_intent.gateway_payment_id}/'
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Payment intent creation failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to create payment intent'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def simulate(self, request, pk=None):
        """
        Simulate payment success (for testing/demo purposes)
        In production, this endpoint would not exist
        """
        payment_intent = self.get_object()
        
        if payment_intent.status != PaymentIntent.PaymentStatus.PENDING:
            return Response(
                {'error': 'Payment already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_method = request.data.get('payment_method', 'CARD')
        
        try:
            webhook_event = PaymentService.simulate_payment_success(
                payment_intent,
                payment_method=payment_method
            )
            
            # Refresh payment intent
            payment_intent.refresh_from_db()
            
            return Response(
                {
                    'message': 'Payment processed successfully',
                    'payment_intent': PaymentIntentSerializer(payment_intent).data,
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Payment simulation failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Payment processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_handler(request):
    """
    Webhook endpoint for payment gateway callbacks
    In production, this should verify webhook signatures
    """
    try:
        # Get webhook data
        payload = json.loads(request.body)
        
        # Verify signature (commented out for demo - enable in production)
        # signature = request.headers.get('X-Webhook-Signature')
        # if not PaymentService.verify_webhook_signature(payload, signature):
        #     logger.warning("Invalid webhook signature")
        #     return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        logger.info(f"Webhook received: {payload.get('event')}")
        
        # Process webhook asynchronously with Celery
        process_webhook_async.delay(payload)
        
        return JsonResponse({'status': 'received'}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Processing failed'}, status=500)
