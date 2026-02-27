"""
Celery tasks for payments
"""
from celery import shared_task
import logging

logger = logging.getLogger('payments')


@shared_task(bind=True, max_retries=3)
def process_webhook_async(self, payload):
    """
    Process payment webhook asynchronously
    Implements retry logic for failed webhooks
    """
    try:
        from .services import PaymentService
        
        webhook_event = PaymentService.process_payment_webhook(payload)
        logger.info(f"Webhook processed successfully: {webhook_event.event_id}")
        
        return {
            'status': 'success',
            'event_id': str(webhook_event.event_id)
        }
        
    except Exception as exc:
        logger.error(f"Webhook processing failed: {str(exc)}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def cleanup_old_webhook_events():
    """
    Cleanup old processed webhook events (run periodically)
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import WebhookEvent
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count, _ = WebhookEvent.objects.filter(
        status=WebhookEvent.EventStatus.PROCESSED,
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old webhook events")
    
    return {'deleted_count': deleted_count}
