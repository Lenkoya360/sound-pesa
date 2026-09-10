"""
Celery tasks for transaction processing and monitoring.
"""
import logging
from decimal import Decimal
from typing import List, Dict, Any
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from celery import shared_task
from celery.exceptions import Retry

from .models import Transaction, NetworkFeeRate
from .services import TransactionProcessingService, TransactionMonitoringService
from apps.blockchain.adapters.factory import BlockchainAdapterFactory
from apps.blockchain.models import BlockchainNode

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_transaction_task(self, transaction_id: str):
    """
    Process a transaction by signing and broadcasting it to the blockchain.
    
    Args:
        transaction_id: UUID of the transaction to process
        
    Returns:
        dict: Processing result with status and details
    """
    try:
        logger.info(f"Processing transaction {transaction_id}")
        
        # Process the transaction
        success = TransactionProcessingService.process_transaction(transaction_id)
        
        if success:
            logger.info(f"Transaction {transaction_id} processed successfully")
            return {
                'status': 'success',
                'transaction_id': transaction_id,
                'message': 'Transaction processed and broadcasted'
            }
        else:
            # Retry if processing failed
            logger.warning(f"Transaction {transaction_id} processing failed, retrying...")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
            
    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        return {
            'status': 'error',
            'transaction_id': transaction_id,
            'message': 'Transaction not found'
        }
    except Exception as exc:
        logger.error(f"Transaction {transaction_id} processing error: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        else:
            # Mark transaction as failed after max retries
            try:
                transaction = Transaction.objects.get(id=transaction_id)
                transaction.status = 'failed'
                transaction.error_message = f"Processing failed after {self.max_retries} retries: {str(exc)}"
                transaction.save()
            except Transaction.DoesNotExist:
                pass
            
            return {
                'status': 'failed',
                'transaction_id': transaction_id,
                'message': f'Transaction processing failed after {self.max_retries} retries'
            }


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def update_transaction_status_task(self, transaction_id: str):
    """
    Update transaction status by checking the blockchain.
    
    Args:
        transaction_id: UUID of the transaction to update
        
    Returns:
        dict: Update result with status and details
    """
    try:
        logger.debug(f"Updating transaction status for {transaction_id}")
        
        updated = TransactionMonitoringService.update_transaction_status(transaction_id)
        
        if updated:
            logger.info(f"Transaction {transaction_id} status updated")
            return {
                'status': 'updated',
                'transaction_id': transaction_id,
                'message': 'Transaction status updated from blockchain'
            }
        else:
            return {
                'status': 'no_change',
                'transaction_id': transaction_id,
                'message': 'No status change detected'
            }
            
    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        return {
            'status': 'error',
            'transaction_id': transaction_id,
            'message': 'Transaction not found'
        }
    except Exception as exc:
        logger.error(f"Transaction {transaction_id} status update error: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        else:
            return {
                'status': 'failed',
                'transaction_id': transaction_id,
                'message': f'Status update failed after {self.max_retries} retries'
            }


@shared_task
def monitor_pending_transactions():
    """
    Monitor all pending transactions and update their status.
    
    This task runs periodically to check pending transactions against
    the blockchain and update their confirmation status.
    
    Returns:
        dict: Monitoring result with statistics
    """
    try:
        logger.info("Starting pending transactions monitoring")
        
        # Get pending transactions with transaction hashes
        pending_transactions = Transaction.objects.filter(
            status='pending',
            transaction_hash__isnull=False
        ).values_list('id', flat=True)
        
        total_transactions = len(pending_transactions)
        updated_count = 0
        failed_count = 0
        
        # Process each transaction asynchronously
        for transaction_id in pending_transactions:
            try:
                # Queue status update task
                update_transaction_status_task.delay(str(transaction_id))
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to queue status update for {transaction_id}: {str(e)}")
                failed_count += 1
        
        result = {
            'status': 'completed',
            'total_transactions': total_transactions,
            'queued_updates': updated_count,
            'failed_to_queue': failed_count,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Pending transactions monitoring completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Pending transactions monitoring failed: {str(exc)}")
        return {
            'status': 'failed',
            'message': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def cleanup_expired_estimates():
    """
    Clean up expired transaction estimates.
    
    This task runs periodically to remove expired transaction estimates
    to keep the database clean.
    
    Returns:
        dict: Cleanup result with statistics
    """
    try:
        logger.info("Starting expired estimates cleanup")
        
        # Delete estimates that expired more than 1 hour ago
        cutoff_time = timezone.now() - timedelta(hours=1)
        
        from .models import TransactionEstimate
        deleted_count, _ = TransactionEstimate.objects.filter(
            expires_at__lt=cutoff_time
        ).delete()
        
        result = {
            'status': 'completed',
            'deleted_estimates': deleted_count,
            'cutoff_time': cutoff_time.isoformat(),
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Expired estimates cleanup completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Expired estimates cleanup failed: {str(exc)}")
        return {
            'status': 'failed',
            'message': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_network_fee_rates(self):
    """
    Update network fee rates for all supported blockchains.
    
    This task runs periodically to fetch current fee rates from
    blockchain networks and update the database.
    
    Returns:
        dict: Update result with statistics
    """
    try:
        logger.info("Starting network fee rates update")
        
        updated_blockchains = []
        failed_blockchains = []
        
        # Get all supported blockchains
        supported_blockchains = BlockchainAdapterFactory.get_supported_blockchains()
        
        for blockchain in supported_blockchains:
            try:
                # Get blockchain adapter
                adapter = BlockchainAdapterFactory.get_adapter(blockchain)
                
                # Fetch current fee rates (this would be implemented in each adapter)
                fee_rates = await _fetch_network_fee_rates(adapter, blockchain)
                
                # Update or create network fee rate record
                network_fee, created = NetworkFeeRate.objects.update_or_create(
                    blockchain=blockchain,
                    defaults={
                        'low_fee_rate': fee_rates['low'],
                        'medium_fee_rate': fee_rates['medium'],
                        'high_fee_rate': fee_rates['high'],
                        'mempool_size': fee_rates.get('mempool_size', 0),
                        'average_confirmation_time': fee_rates.get('avg_confirmation_time', 10),
                        'congestion_level': fee_rates.get('congestion_level', 'medium')
                    }
                )
                
                updated_blockchains.append(blockchain)
                logger.info(f"Updated fee rates for {blockchain}")
                
            except Exception as e:
                logger.error(f"Failed to update fee rates for {blockchain}: {str(e)}")
                failed_blockchains.append({'blockchain': blockchain, 'error': str(e)})
        
        result = {
            'status': 'completed',
            'updated_blockchains': updated_blockchains,
            'failed_blockchains': failed_blockchains,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Network fee rates update completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Network fee rates update failed: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries), exc=exc)
        else:
            return {
                'status': 'failed',
                'message': f'Fee rates update failed after {self.max_retries} retries',
                'timestamp': timezone.now().isoformat()
            }


@shared_task
def monitor_blockchain_nodes():
    """
    Monitor blockchain node health and synchronization status.
    
    This task runs periodically to check if blockchain nodes are
    healthy and synchronized.
    
    Returns:
        dict: Monitoring result with node status
    """
    try:
        logger.info("Starting blockchain nodes monitoring")
        
        node_status = {}
        healthy_nodes = 0
        unhealthy_nodes = 0
        
        # Get all blockchain nodes
        nodes = BlockchainNode.objects.all()
        
        for node in nodes:
            try:
                # Get blockchain adapter
                adapter = BlockchainAdapterFactory.get_adapter(node.blockchain)
                
                # Check node status
                is_synced = await adapter.is_node_synced()
                current_block = await adapter.get_block_height()
                
                # Update node status
                node.is_synced = is_synced
                node.current_block_height = current_block
                node.last_checked = timezone.now()
                node.save()
                
                node_status[node.blockchain] = {
                    'is_synced': is_synced,
                    'block_height': current_block,
                    'network': node.network,
                    'status': 'healthy' if is_synced else 'syncing'
                }
                
                if is_synced:
                    healthy_nodes += 1
                else:
                    unhealthy_nodes += 1
                    
                logger.info(f"{node.blockchain} node status: synced={is_synced}, block={current_block}")
                
            except Exception as e:
                logger.error(f"Failed to check {node.blockchain} node: {str(e)}")
                
                node_status[node.blockchain] = {
                    'status': 'error',
                    'error': str(e)
                }
                unhealthy_nodes += 1
        
        result = {
            'status': 'completed',
            'healthy_nodes': healthy_nodes,
            'unhealthy_nodes': unhealthy_nodes,
            'node_details': node_status,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Blockchain nodes monitoring completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Blockchain nodes monitoring failed: {str(exc)}")
        return {
            'status': 'failed',
            'message': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def retry_failed_transactions():
    """
    Retry failed transactions that might be recoverable.
    
    This task runs periodically to identify failed transactions that
    might be retryable and queue them for processing again.
    
    Returns:
        dict: Retry result with statistics
    """
    try:
        logger.info("Starting failed transactions retry")
        
        # Get failed transactions that are less than 24 hours old
        # and have been retried less than 3 times
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        failed_transactions = Transaction.objects.filter(
            status='failed',
            created_at__gte=cutoff_time,
            retry_count__lt=3,
            error_message__icontains='network'  # Only retry network-related failures
        )
        
        retried_count = 0
        skipped_count = 0
        
        for transaction in failed_transactions:
            try:
                # Reset transaction status to pending
                transaction.status = 'pending'
                transaction.retry_count += 1
                transaction.last_retry_at = timezone.now()
                transaction.error_message = ''
                transaction.save()
                
                # Queue for processing
                process_transaction_task.delay(str(transaction.id))
                retried_count += 1
                
                logger.info(f"Queued transaction {transaction.id} for retry (attempt {transaction.retry_count})")
                
            except Exception as e:
                logger.error(f"Failed to retry transaction {transaction.id}: {str(e)}")
                skipped_count += 1
        
        result = {
            'status': 'completed',
            'retried_transactions': retried_count,
            'skipped_transactions': skipped_count,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Failed transactions retry completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Failed transactions retry failed: {str(exc)}")
        return {
            'status': 'failed',
            'message': str(exc),
            'timestamp': timezone.now().isoformat()
        }


async def _fetch_network_fee_rates(adapter, blockchain: str) -> Dict[str, Any]:
    """
    Fetch current network fee rates from blockchain adapter.
    
    This is a helper function that would be implemented differently
    for each blockchain type.
    
    Args:
        adapter: Blockchain adapter instance
        blockchain: Blockchain name
        
    Returns:
        dict: Fee rates and network information
    """
    # This would be implemented with actual blockchain API calls
    # For now, return mock data based on blockchain type
    
    if blockchain == 'bitcoin':
        return {
            'low': '0.00001',
            'medium': '0.0001',
            'high': '0.001',
            'mempool_size': 50000,
            'avg_confirmation_time': 30,
            'congestion_level': 'medium'
        }
    elif blockchain == 'ethereum':
        return {
            'low': '20000000000',  # 20 Gwei
            'medium': '30000000000',  # 30 Gwei
            'high': '50000000000',  # 50 Gwei
            'mempool_size': 100000,
            'avg_confirmation_time': 2,
            'congestion_level': 'medium'
        }
    elif blockchain == 'cardano':
        return {
            'low': '0.155381',
            'medium': '0.170000',
            'high': '0.200000',
            'mempool_size': 5000,
            'avg_confirmation_time': 5,
            'congestion_level': 'low'
        }
    elif blockchain == 'polkadot':
        return {
            'low': '0.01',
            'medium': '0.02',
            'high': '0.05',
            'mempool_size': 1000,
            'avg_confirmation_time': 1,
            'congestion_level': 'low'
        }
    else:
        return {
            'low': '0.001',
            'medium': '0.01',
            'high': '0.1',
            'mempool_size': 0,
            'avg_confirmation_time': 10,
            'congestion_level': 'medium'
        }