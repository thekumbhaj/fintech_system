"""
Signals for wallet app - auto-create wallet on user creation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wallet
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet_for_user(sender, instance, created, **kwargs):
    """
    Automatically create a wallet when a new user is created
    """
    if created:
        wallet = Wallet.objects.create(user=instance)
        logger.info(f"Wallet created for user: {instance.email} - Wallet ID: {wallet.id}")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_wallet_for_user(sender, instance, **kwargs):
    """
    Ensure wallet exists for user (fallback)
    """
    if not hasattr(instance, 'wallet'):
        wallet = Wallet.objects.create(user=instance)
        logger.info(f"Wallet created (fallback) for user: {instance.email} - Wallet ID: {wallet.id}")
