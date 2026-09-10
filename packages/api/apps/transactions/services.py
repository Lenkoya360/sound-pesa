"""
Transaction processing services for Sound Pesa platform.
"""
import uuid
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from datetime import timedelta
from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.cache import cache

from .models import (
    Transaction, TransactionEstimate, TransactionAuditLog,
    TransactionLock, NetworkFeeRate
)
from apps.wallets.models import Wallet, WalletBalance
from apps.blockchain.adapters.factory import BlockchainAdapterFactory
from sound_pesa.exceptions import ValidationError, BlockchainError

logger = logging.getLogger(__name__)


class TransactionEstimationService:
    """
    Service for handling transaction fee estimation.
    """
    
    @staticmethod
    async def estimate_transaction_fee(
        user,
        from_wallet_id: str,
        to_address: str,
        amount: str,
        fee_priority: str = 'medium'
    ) -> TransactionEstimate:
        """
        Estimate transaction fee for a given transaction.
        
        Args:
            user: User making the request
            from_wallet_id: Source wallet ID
            to_address: Destination address
            amount: Amount to transfer
            fee_priority: Fee priority level
            
        Returns:
            TransactionEstimate instance
            
        Raises:
            ValidationError: If validation fails
            BlockchainError: If blockchain interaction fails
        """
        try:
            # Get wallet and validate ownership
            wallet = Wallet.objects.get(id=from_wallet_id, user=user, is_active=True)
            
            # Get blockchain adapter
            adapter = BlockchainAdapterFactory.get_adapter(wallet.blockchain)
            
            # Validate address
            if not adapter.validate_address(to_address):
                raise ValidationError(f"Invalid {wallet.blockchain} address format")
            
            # Get current network fee rates
            fee_rates = await TransactionEstimationService._get_network_fee_rates(wallet.blockchain)
            
            # Estimate fee using blockchain adapter
            estimated_fee = await adapter.estimate_fee(
                wallet.address, to_address, amount
            )
            
            # Adjust fee based on priority
            priority_multipliers = {'low': 0.8, 'medium': 1.0, 'high': 1.5}
            multiplier = priority_multipliers.get(fee_priority, 1.0)
            adjusted_fee = str(Decimal(estimated_fee) * Decimal(str(multiplier)))
            
            # Estimate confirmation time based on network congestion
            confirmation_time = TransactionEstimationService._estimate_confirmation_time(
                wallet.blockchain, fee_priority
            )
            
            # Create estimate record
            estimate = TransactionEstimate.objects.create(
                blockchain=wallet.blockchain,
                amount=amount,
                estimated_fee=adjusted_fee,
                fee_priority=fee_priority,
                estimated_confirmation_time=confirmation_time,
                network_congestion=fee_rates.get('congestion_level', 'medium'),
                user=user,
                expires_at=timezone.now() + timedelta(minutes=15)  # 15-minute expiry
            )
            
            # Add blockchain-specific data
            if wallet.blockchain == 'ethereum':
                gas_data = await TransactionEstimationService._estimate_ethereum_gas(
                    adapter, wallet.address, to_address, amount
                )
                estimate.gas_limit = gas_data['gas_limit']
                estimate.gas_price = gas_data['gas_price']
                estimate.save()
            elif wallet.blockchain == 'bitcoin':
                sat_per_byte = await TransactionEstimationService._estimate_bitcoin_fee_rate(
                    adapter, fee_priority
                )
                estimate.sat_per_byte = sat_per_byte
                estimate.save()
            
            logger.info(f"Fee estimated for {wallet.blockchain}: {adjusted_fee}")
            return estimate
            
        except Wallet.DoesNotExist:
            raise ValidationError("Wallet not found or not accessible")
        except Exception as e:
            logger.error(f"Fee estimation failed: {str(e)}")
            raise BlockchainError(f"Failed to estimate transaction fee: {str(e)}")
    
    @staticmethod
    async def _get_network_fee_rates(blockchain: str) -> Dict[str, Any]:
        """Get current network fee rates from cache or database."""
        cache_key = f"network_fee_rates_{blockchain}"
        fee_rates = cache.get(cache_key)
        
        if not fee_rates:
            try:
                network_fee = NetworkFeeRate.objects.get(blockchain=blockchain)
                fee_rates = {
                    'low': str(network_fee.low_fee_rate),
                    'medium': str(network_fee.medium_fee_rate),
                    'high': str(network_fee.high_fee_rate),
                    'congestion_level': network_fee.congestion_level
                }
                cache.set(cache_key, fee_rates, 300)  # 5-minute cache
            except NetworkFeeRate.DoesNotExist:
                # Default fee rates if not in database
                fee_rates = {
                    'low': '0.00001',
                    'medium': '0.0001',
                    'high': '0.001',
                    'congestion_level': 'medium'
                }
        
        return fee_rates
    
    @staticmethod
    def _estimate_confirmation_time(blockchain: str, fee_priority: str) -> int:
        """Estimate confirmation time in minutes based on blockchain and priority."""
        base_times = {
            'bitcoin': {'low': 60, 'medium': 30, 'high': 10},
            'ethereum': {'low': 5, 'medium': 2, 'high': 1},
            'cardano': {'low': 10, 'medium': 5, 'high': 2},
            'polkadot': {'low': 2, 'medium': 1, 'high': 1}
        }
        
        return base_times.get(blockchain, {}).get(fee_priority, 10)
    
    @staticmethod
    async def _estimate_ethereum_gas(adapter, from_addr: str, to_addr: str, amount: str) -> Dict[str, Any]:
        """Estimate Ethereum gas limit and price."""
        # This would integrate with the Ethereum adapter's gas estimation
        # For now, return reasonable defaults
        return {
            'gas_limit': 21000,  # Standard ETH transfer
            'gas_price': '20000000000'  # 20 Gwei
        }
    
    @staticmethod
    async def _estimate_bitcoin_fee_rate(adapter, fee_priority: str) -> Decimal:
        """Estimate Bitcoin fee rate in satoshis per byte."""
        priority_rates = {'low': 1, 'medium': 5, 'high': 10}
        return Decimal(str(priority_rates.get(fee_priority, 5)))


class TransactionCreationService:
    """
    Service for creating and validating transactions.
    """
    
    @staticmethod
    async def create_transaction(
        user,
        from_wallet_id: str,
        to_address: str,
        amount: str,
        fee_priority: str = 'medium',
        estimate_id: Optional[str] = None
    ) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            user: User creating the transaction
            from_wallet_id: Source wallet ID
            to_address: Destination address
            amount: Amount to transfer
            fee_priority: Fee priority level
            estimate_id: Optional estimate ID to use
            
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: If validation fails
            BlockchainError: If blockchain interaction fails
        """
        correlation_id = uuid.uuid4()
        
        try:
            with db_transaction.atomic():
                # Get and validate wallet
                wallet = Wallet.objects.select_for_update().get(
                    id=from_wallet_id, user=user, is_active=True
                )
                
                # Validate balance
                await TransactionCreationService._validate_wallet_balance(
                    wallet, amount, correlation_id
                )
                
                # Get or create fee estimate
                if estimate_id:
                    estimate = TransactionEstimate.objects.get(
                        id=estimate_id, user=user, is_used=False
                    )
                    if estimate.is_expired:
                        raise ValidationError("Transaction estimate has expired")
                    
                    # Mark estimate as used
                    estimate.is_used = True
                    estimate.save()
                    
                    estimated_fee = estimate.estimated_fee
                else:
                    # Create new estimate
                    estimate = await TransactionEstimationService.estimate_transaction_fee(
                        user, from_wallet_id, to_address, amount, fee_priority
                    )
                    estimated_fee = estimate.estimated_fee
                
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    user=user,
                    from_wallet=wallet,
                    to_address=to_address,
                    blockchain=wallet.blockchain,
                    amount=amount,
                    fee=estimated_fee,
                    status='pending',
                    correlation_id=correlation_id
                )
                
                # Copy blockchain-specific data from estimate
                if estimate.gas_limit:
                    transaction_obj.gas_limit = estimate.gas_limit
                if estimate.gas_price:
                    transaction_obj.gas_price = estimate.gas_price
                if estimate.sat_per_byte:
                    # Store in metadata for Bitcoin transactions
                    pass
                
                transaction_obj.save()
                
                # Create audit log
                TransactionAuditLog.objects.create(
                    transaction=transaction_obj,
                    correlation_id=correlation_id,
                    action='created',
                    user=user,
                    message=f"Transaction created for {amount} {wallet.blockchain}"
                )
                
                logger.info(f"Transaction created: {transaction_obj.id}")
                return transaction_obj
                
        except Wallet.DoesNotExist:
            raise ValidationError("Wallet not found or not accessible")
        except TransactionEstimate.DoesNotExist:
            raise ValidationError("Transaction estimate not found")
        except Exception as e:
            logger.error(f"Transaction creation failed: {str(e)}")
            raise BlockchainError(f"Failed to create transaction: {str(e)}")
    
    @staticmethod
    async def _validate_wallet_balance(wallet: Wallet, amount: str, correlation_id: uuid.UUID):
        """Validate that wallet has sufficient balance."""
        try:
            balance = wallet.balance
            required_amount = Decimal(amount)
            
            if balance.confirmed_balance < required_amount:
                raise ValidationError("Insufficient confirmed balance")
            
            # Check for pending transactions that might affect balance
            pending_amount = await TransactionCreationService._get_pending_outgoing_amount(wallet)
            available_balance = balance.confirmed_balance - pending_amount
            
            if available_balance < required_amount:
                raise ValidationError("Insufficient available balance (pending transactions)")
                
        except WalletBalance.DoesNotExist:
            raise ValidationError("Wallet balance not found")
    
    @staticmethod
    async def _get_pending_outgoing_amount(wallet: Wallet) -> Decimal:
        """Get total amount of pending outgoing transactions."""
        from django.db.models import Sum
        
        pending_sum = Transaction.objects.filter(
            from_wallet=wallet,
            status='pending'
        ).aggregate(total=Sum('amount'))['total']
        
        return pending_sum or Decimal('0')


class TransactionProcessingService:
    """
    Service for processing and broadcasting transactions.
    """
    
    @staticmethod
    async def process_transaction(transaction_id: str) -> bool:
        """
        Process a transaction by signing and broadcasting it.
        
        Args:
            transaction_id: Transaction ID to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get transaction with lock
            with TransactionProcessingService._acquire_transaction_lock(transaction_id):
                transaction_obj = Transaction.objects.get(id=transaction_id)
                
                if transaction_obj.status != 'pending':
                    logger.warning(f"Transaction {transaction_id} is not pending")
                    return False
                
                # Get blockchain adapter
                adapter = BlockchainAdapterFactory.get_adapter(transaction_obj.blockchain)
                
                # Validate transaction before processing
                await TransactionProcessingService._validate_transaction(transaction_obj)
                
                # Sign and broadcast transaction
                tx_hash = await TransactionProcessingService._sign_and_broadcast(
                    transaction_obj, adapter
                )
                
                # Update transaction with hash
                transaction_obj.transaction_hash = tx_hash
                transaction_obj.save()
                
                # Create audit log
                TransactionAuditLog.objects.create(
                    transaction=transaction_obj,
                    correlation_id=transaction_obj.correlation_id,
                    action='broadcasted',
                    message=f"Transaction broadcasted with hash: {tx_hash}"
                )
                
                logger.info(f"Transaction {transaction_id} broadcasted: {tx_hash}")
                return True
                
        except Transaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} not found")
            return False
        except Exception as e:
            logger.error(f"Transaction processing failed: {str(e)}")
            await TransactionProcessingService._handle_transaction_failure(
                transaction_id, str(e)
            )
            return False
    
    @staticmethod
    def _acquire_transaction_lock(transaction_id: str):
        """Acquire a distributed lock for transaction processing."""
        # This would implement distributed locking using Redis or database
        # For now, return a simple context manager
        class TransactionLockContext:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return TransactionLockContext()
    
    @staticmethod
    async def _validate_transaction(transaction_obj: Transaction):
        """Validate transaction before processing."""
        # Re-validate wallet balance
        wallet = transaction_obj.from_wallet
        if hasattr(wallet, 'balance'):
            if wallet.balance.confirmed_balance < transaction_obj.amount:
                raise ValidationError("Insufficient balance at processing time")
        
        # Validate blockchain node is synced
        adapter = BlockchainAdapterFactory.get_adapter(transaction_obj.blockchain)
        if not await adapter.is_node_synced():
            raise BlockchainError("Blockchain node is not synchronized")
    
    @staticmethod
    async def _sign_and_broadcast(transaction_obj: Transaction, adapter) -> str:
        """Sign and broadcast transaction to the blockchain."""
        # This would decrypt the private key from Vault and sign the transaction
        # For now, simulate the process
        
        # Get encrypted private key (would decrypt using Vault)
        private_key = "simulated_private_key"  # This would be decrypted
        
        # Sign and broadcast
        tx_hash = await adapter.send_transaction(
            transaction_obj.from_wallet.address,
            transaction_obj.to_address,
            str(transaction_obj.amount),
            private_key
        )
        
        return tx_hash
    
    @staticmethod
    async def _handle_transaction_failure(transaction_id: str, error_message: str):
        """Handle transaction processing failure."""
        try:
            transaction_obj = Transaction.objects.get(id=transaction_id)
            transaction_obj.status = 'failed'
            transaction_obj.error_message = error_message
            transaction_obj.save()
            
            # Create audit log
            TransactionAuditLog.objects.create(
                transaction=transaction_obj,
                correlation_id=transaction_obj.correlation_id,
                action='failed',
                message=f"Transaction failed: {error_message}"
            )
            
        except Transaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} not found for failure handling")


class TransactionMonitoringService:
    """
    Service for monitoring transaction status and confirmations.
    """
    
    @staticmethod
    async def update_transaction_status(transaction_id: str) -> bool:
        """
        Update transaction status by checking blockchain.
        
        Args:
            transaction_id: Transaction ID to update
            
        Returns:
            True if updated, False otherwise
        """
        try:
            transaction_obj = Transaction.objects.get(id=transaction_id)
            
            if not transaction_obj.transaction_hash:
                return False
            
            # Get blockchain adapter
            adapter = BlockchainAdapterFactory.get_adapter(transaction_obj.blockchain)
            
            # Get transaction details from blockchain
            tx_details = await adapter.get_transaction(transaction_obj.transaction_hash)
            
            # Update transaction based on blockchain data
            updated = False
            
            if tx_details.get('block_height') and not transaction_obj.block_height:
                transaction_obj.block_height = tx_details['block_height']
                updated = True
            
            if tx_details.get('confirmations') != transaction_obj.confirmations:
                transaction_obj.confirmations = tx_details['confirmations']
                updated = True
            
            # Update status based on confirmations
            required_confirmations = 6  # This would be blockchain-specific
            if transaction_obj.confirmations >= required_confirmations:
                if transaction_obj.status != 'confirmed':
                    transaction_obj.status = 'confirmed'
                    updated = True
                    
                    # Create audit log
                    TransactionAuditLog.objects.create(
                        transaction=transaction_obj,
                        correlation_id=transaction_obj.correlation_id,
                        action='confirmed',
                        message=f"Transaction confirmed with {transaction_obj.confirmations} confirmations"
                    )
            
            if updated:
                transaction_obj.save()
                logger.info(f"Transaction {transaction_id} status updated")
            
            return updated
            
        except Transaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} not found")
            return False
        except Exception as e:
            logger.error(f"Transaction status update failed: {str(e)}")
            return False
    
    @staticmethod
    async def monitor_pending_transactions():
        """Monitor all pending transactions for status updates."""
        pending_transactions = Transaction.objects.filter(
            status='pending',
            transaction_hash__isnull=False
        )
        
        updated_count = 0
        for transaction in pending_transactions:
            if await TransactionMonitoringService.update_transaction_status(str(transaction.id)):
                updated_count += 1
        
        logger.info(f"Updated {updated_count} pending transactions")
        return updated_count