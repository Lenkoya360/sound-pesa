"""
Signal handlers for wallet management.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .services import WalletService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallets(sender, instance, created, **kwargs):
    """
    Automatically create wallets for all supported blockchains when a user is created.
    """
    if created:
        try:
            # Create wallets for all supported blockchains
            wallets = WalletService.create_all_wallets(instance)
            logger.info(f"Created {len(wallets)} wallets for new user: {instance.email}")
        except Exception as e:
            logger.error(f"Failed to create wallets for new user {instance.email}: {str(e)}")
            # Don't raise the exception to avoid breaking user creation