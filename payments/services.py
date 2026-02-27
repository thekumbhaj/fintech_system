"""
Service layer for payment processing
"""
from django.conf import settings
from django.db import transaction
import logging
import uuid
import hmac
import hashlib

from .models import PaymentIntent, WebhookEvent
from transactions.services import TransactionService
from users.models import User

logger = logging.getLogger('payments')


class PaymentService:
    """Service class for handling payments"""
    
    @staticmethod
    def generate_payment_id():
        """Generate mock payment gateway ID"""
        return f"PAY-{uuid.uuid4().hex.upper()[:16]}"
    
    @staticmethod
    def create_payment_intent(user, amount, currency='USD', description=''):
        """
        Create a payment intent (simulates payment gateway)
        In production, this would call actual payment gateway API
        """
        gateway_payment_id = PaymentService.generate_payment_id()
        
        payment_intent = PaymentIntent.objects.create(
            gateway_payment_id=gateway_payment_id,
            user=user,
            amount=amount,
            currency=currency,
            description=description,
            status=PaymentIntent.PaymentStatus.PENDING,
        )
        
        logger.info(
            f"Payment intent created: {gateway_payment_id} | "
            f"User: {user.email} | Amount: {amount} {currency}"
        )
        
        return payment_intent
    
    @staticmethod
    def simulate_payment_success(payment_intent, payment_method='CARD'):
        """
        Simulate successful payment (for testing/demo)
        In production, payment gateway would send webhook
        """
        payment_intent.payment_method = payment_method
        payment_intent.status = PaymentIntent.PaymentStatus.PROCESSING
        payment_intent.save()
        
        # Simulate webhook payload
        webhook_payload = {
            'event': 'payment.succeeded',
            'payment_id': payment_intent.gateway_payment_id,
            'amount': float(payment_intent.amount),
            'currency': payment_intent.currency,
            'user_email': payment_intent.user.email,
            'payment_method': payment_method,
        }
        
        # Process webhook
        return PaymentService.process_payment_webhook(webhook_payload)
    
    @staticmethod
    @transaction.atomic
    def process_payment_webhook(payload):
        """
        Process payment webhook from gateway
        Implements idempotent webhook processing
        """
        event_id = payload.get('payment_id')  # Use payment_id as event_id for simplicity
        event_type = payload.get('event', 'payment.succeeded')
        
        # Check if webhook already processed (idempotency)
        existing_event = WebhookEvent.objects.filter(event_id=event_id).first()
        if existing_event and existing_event.status == WebhookEvent.EventStatus.PROCESSED:
            logger.info(f"Webhook already processed: {event_id}")
            return existing_event
        
        # Create webhook event record
        if not existing_event:
            webhook_event = WebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                status=WebhookEvent.EventStatus.PROCESSING,
            )
        else:
            webhook_event = existing_event
            webhook_event.status = WebhookEvent.EventStatus.PROCESSING
            webhook_event.save()
        
        try:
            # Get payment intent
            payment_id = payload.get('payment_id')
            payment_intent = PaymentIntent.objects.get(gateway_payment_id=payment_id)
            
            # Update payment intent
            payment_intent.gateway_response = payload
            
            if event_type == 'payment.succeeded':
                payment_intent.mark_succeeded()
                
                # Add money to user wallet
                transaction_ref = f"DEPOSIT-{payment_intent.gateway_payment_id}"
                TransactionService.add_money(
                    user=payment_intent.user,
                    amount=payment_intent.amount,
                    description=f"Deposit via {payment_intent.payment_method}",
                    reference_id=transaction_ref,
                )
                
                logger.info(
                    f"Payment processed successfully: {payment_id} | "
                    f"User: {payment_intent.user.email} | Amount: {payment_intent.amount}"
                )
                
            elif event_type == 'payment.failed':
                error_message = payload.get('error_message', 'Payment failed')
                payment_intent.mark_failed(error_message)
                logger.warning(f"Payment failed: {payment_id} - {error_message}")
            
            # Mark webhook as processed
            webhook_event.mark_processed()
            
            return webhook_event
            
        except PaymentIntent.DoesNotExist:
            error_msg = f"Payment intent not found: {payment_id}"
            webhook_event.mark_failed(error_msg)
            logger.error(error_msg)
            raise
            
        except Exception as e:
            error_msg = f"Webhook processing failed: {str(e)}"
            webhook_event.mark_failed(error_msg)
            logger.error(error_msg, exc_info=True)
            raise
    
    @staticmethod
    def verify_webhook_signature(payload, signature, secret=None):
        """
        Verify webhook signature for security
        Implements HMAC verification
        """
        if secret is None:
            secret = settings.PAYMENT_GATEWAY_WEBHOOK_SECRET
        
        # Calculate expected signature
        payload_string = str(payload)
        expected_signature = hmac.new(
            secret.encode(),
            payload_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
