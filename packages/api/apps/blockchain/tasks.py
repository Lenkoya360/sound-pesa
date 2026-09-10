"""
Celery tasks for blockchain monitoring and metrics collection.
"""
from celery import shared_task
from django.utils import timezone
from sound_pesa.metrics import (
    update_blockchain_metrics,
    blockchain_sync_lag_blocks,
    blockchain_peer_count,
    blockchain_last_block_time,
    active_wallets_count
)
from .services import BlockchainService
from apps.wallets.models import Wallet
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_blockchain_metrics(self):
    """
    Collect metrics from all blockchain nodes.
    This task runs periodically to update Prometheus metrics.
    """
    try:
        blockchain_service = BlockchainService()
        supported_blockchains = ['bitcoin', 'ethereum', 'cardano', 'polkadot']
        
        for blockchain in supported_blockchains:
            try:
                # Get blockchain status
                status = blockchain_service.get_blockchain_status_sync(blockchain)
                
                if status:
                    # Calculate sync lag
                    sync_lag = max(0, status.get('highest_block', 0) - status.get('current_block', 0))
                    
                    # Update metrics
                    update_blockchain_metrics(
                        blockchain=blockchain,
                        sync_lag=sync_lag,
                        peer_count=status.get('peer_count', 0),
                        last_block_time=status.get('last_block_time', timezone.now().timestamp())
                    )
                    
                    # Update active wallets count
                    active_wallets = Wallet.objects.filter(
                        blockchain=blockchain,
                        is_active=True
                    ).count()
                    
                    active_wallets_count.labels(blockchain=blockchain).set(active_wallets)
                    
                    logger.info(f"Updated metrics for {blockchain}: sync_lag={sync_lag}, peers={status.get('peer_count', 0)}")
                
            except Exception as e:
                logger.error(f"Failed to collect metrics for {blockchain}: {str(e)}")
                continue
                
        return "Blockchain metrics collection completed"
        
    except Exception as exc:
        logger.error(f"Blockchain metrics collection failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def collect_transaction_queue_metrics(self):
    """
    Collect transaction queue metrics for monitoring.
    """
    try:
        from apps.transactions.models import Transaction
        from sound_pesa.metrics import transaction_queue_size
        
        # Count pending transactions
        pending_count = Transaction.objects.filter(status='pending').count()
        transaction_queue_size.set(pending_count)
        
        logger.info(f"Updated transaction queue metrics: pending={pending_count}")
        return f"Transaction queue metrics updated: {pending_count} pending"
        
    except Exception as exc:
        logger.error(f"Transaction queue metrics collection failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def collect_wallet_balance_metrics(self):
    """
    Collect wallet balance metrics for monitoring.
    """
    try:
        from apps.wallets.models import Wallet, WalletBalance
        from sound_pesa.metrics import update_wallet_metrics
        
        # Get recent wallet balances
        recent_balances = WalletBalance.objects.select_related('wallet').filter(
            last_updated__gte=timezone.now() - timezone.timedelta(hours=1)
        )
        
        for balance in recent_balances:
            update_wallet_metrics(
                blockchain=balance.wallet.blockchain,
                wallet_id=str(balance.wallet.id),
                balance=balance.balance
            )
        
        logger.info(f"Updated wallet balance metrics for {recent_balances.count()} wallets")
        return f"Wallet balance metrics updated for {recent_balances.count()} wallets"
        
    except Exception as exc:
        logger.error(f"Wallet balance metrics collection failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def health_check_blockchain_nodes(self):
    """
    Perform health checks on blockchain nodes and update status.
    """
    try:
        blockchain_service = BlockchainService()
        supported_blockchains = ['bitcoin', 'ethereum', 'cardano', 'polkadot']
        results = {}
        
        for blockchain in supported_blockchains:
            try:
                # Perform basic connectivity test
                status = blockchain_service.get_blockchain_status_sync(blockchain)
                is_healthy = status is not None and status.get('is_synced', False)
                
                results[blockchain] = {
                    'healthy': is_healthy,
                    'sync_percentage': status.get('sync_percentage', 0) if status else 0,
                    'peer_count': status.get('peer_count', 0) if status else 0
                }
                
                logger.info(f"Health check for {blockchain}: {'healthy' if is_healthy else 'unhealthy'}")
                
            except Exception as e:
                logger.error(f"Health check failed for {blockchain}: {str(e)}")
                results[blockchain] = {'healthy': False, 'error': str(e)}
        
        return results
        
    except Exception as exc:
        logger.error(f"Blockchain health check failed: {str(exc)}")
        return {'error': str(exc)}