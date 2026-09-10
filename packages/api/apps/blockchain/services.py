"""
Blockchain services for high-level operations
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone

from .adapters import BlockchainAdapterFactory
from .models import BlockchainNode, BlockchainTransaction, BlockchainAddress
from .config import BlockchainConfig

logger = logging.getLogger(__name__)


class BlockchainService:
    """
    High-level service for blockchain operations
    """

    @staticmethod
    def _is_supported(blockchain: str) -> bool:
        """Return whether a blockchain name is supported."""
        return BlockchainAdapterFactory.is_supported(blockchain)

    @staticmethod
    async def get_balance(user: User, blockchain: str, address: str) -> str:
        """
        Get balance for a user's address on a specific blockchain
        
        Args:
            user: User instance
            blockchain: Blockchain name
            address: Blockchain address
            
        Returns:
            Balance as string
        """
        try:
            adapter = BlockchainAdapterFactory.get_adapter(blockchain)
            balance = await adapter.get_balance(address)
            
            logger.info(f"Retrieved balance for {user.username} on {blockchain}: {balance}")
            return balance
        
        except Exception as e:
            logger.error(f"Failed to get balance for {user.username} on {blockchain}: {str(e)}")
            return '0'
    
    @staticmethod
    async def send_transaction(user: User, blockchain: str, from_address: str, 
                             to_address: str, amount: str, private_key: str) -> str:
        """
        Send a transaction on the specified blockchain
        
        Args:
            user: User instance
            blockchain: Blockchain name
            from_address: Source address
            to_address: Destination address
            amount: Amount to send
            private_key: Private key for signing
            
        Returns:
            Transaction hash
        """
        try:
            adapter = BlockchainAdapterFactory.get_adapter(blockchain)
            
            # Validate addresses
            if not adapter.validate_address(from_address):
                raise ValueError(f"Invalid from_address for {blockchain}")
            
            if not adapter.validate_address(to_address):
                raise ValueError(f"Invalid to_address for {blockchain}")
            
            # Validate amount
            if not adapter.validate_amount(amount):
                raise ValueError(f"Invalid amount: {amount}")
            
            # Check balance
            balance = await adapter.get_balance(from_address)
            if Decimal(balance) < Decimal(amount):
                raise ValueError("Insufficient balance")
            
            # Estimate fee
            fee = await adapter.estimate_fee(from_address, to_address, amount)
            
            # Send transaction
            tx_hash = await adapter.send_transaction(from_address, to_address, amount, private_key)
            
            # Create transaction record
            BlockchainTransaction.objects.create(
                user=user,
                blockchain=blockchain,
                transaction_hash=tx_hash,
                from_address=from_address,
                to_address=to_address,
                amount=Decimal(amount),
                fee=Decimal(fee),
                status='pending'
            )
            
            logger.info(f"Transaction sent for {user.username} on {blockchain}: {tx_hash}")
            return tx_hash
        
        except Exception as e:
            logger.error(f"Failed to send transaction for {user.username} on {blockchain}: {str(e)}")
            raise
    
    @staticmethod
    async def estimate_transaction_fee(blockchain: str, from_address: str, 
                                     to_address: str, amount: str) -> str:
        """
        Estimate transaction fee
        
        Args:
            blockchain: Blockchain name
            from_address: Source address
            to_address: Destination address
            amount: Amount to send
            
        Returns:
            Estimated fee as string
        """
        try:
            adapter = BlockchainAdapterFactory.get_adapter(blockchain)
            return await adapter.estimate_fee(from_address, to_address, amount)
        
        except Exception as e:
            logger.error(f"Failed to estimate fee for {blockchain}: {str(e)}")
            return '0'
    
    @staticmethod
    async def generate_address(user: User, blockchain: str) -> Dict[str, str]:
        """
        Generate a new address for a user on the specified blockchain
        
        Args:
            user: User instance
            blockchain: Blockchain name
            
        Returns:
            Dictionary with 'address' and 'private_key'
        """
        try:
            adapter = BlockchainAdapterFactory.get_adapter(blockchain)
            address_info = await adapter.generate_address()
            
            # Store address in database (private key should be encrypted)
            BlockchainAddress.objects.create(
                user=user,
                blockchain=blockchain,
                address=address_info['address'],
                encrypted_private_key=address_info['private_key']  # Should be encrypted with Vault
            )
            
            logger.info(f"Generated address for {user.username} on {blockchain}: {address_info['address']}")
            return address_info
        
        except Exception as e:
            logger.error(f"Failed to generate address for {user.username} on {blockchain}: {str(e)}")
            raise
    
    @staticmethod
    async def get_transaction_status(tx_hash: str, blockchain: str) -> Dict[str, Any]:
        """
        Get transaction status and details
        
        Args:
            tx_hash: Transaction hash
            blockchain: Blockchain name
            
        Returns:
            Transaction details dictionary
        """
        try:
            adapter = BlockchainAdapterFactory.get_adapter(blockchain)
            tx_details = await adapter.get_transaction(tx_hash)
            
            # Update database record if exists
            try:
                tx_record = BlockchainTransaction.objects.get(transaction_hash=tx_hash)
                tx_record.confirmations = tx_details.get('confirmations', 0)
                tx_record.block_height = tx_details.get('block_height') or tx_details.get('blockNumber')
                tx_record.block_hash = tx_details.get('block_hash') or tx_details.get('blockHash')
                
                # Update status based on confirmations
                required_confirmations = BlockchainConfig.get_config(blockchain)['confirmations_required']
                if tx_record.confirmations >= required_confirmations:
                    tx_record.status = 'confirmed'
                    if not tx_record.confirmed_at:
                        tx_record.confirmed_at = timezone.now()
                
                tx_record.save()
            except BlockchainTransaction.DoesNotExist:
                pass
            
            return tx_details
        
        except Exception as e:
            logger.error(f"Failed to get transaction status for {tx_hash} on {blockchain}: {str(e)}")
            raise
    
    @staticmethod
    async def get_blockchain_status(blockchain: str) -> Dict[str, Any]:
        """
        Get blockchain node status (async version)
        
        Args:
            blockchain: Blockchain name
            
        Returns:
            Blockchain status dictionary
        """
        try:
            adapter = BlockchainAdapterFactory.get_adapter(blockchain)
            status = await adapter.get_network_status()
            
            # Update database record
            node, created = BlockchainNode.objects.get_or_create(
                blockchain=blockchain,
                defaults={
                    'network': status.get('network', 'unknown'),
                    'rpc_url': status.get('rpc_url', ''),
                    'is_synced': status.get('is_synced', False),
                    'current_block_height': status.get('block_height', 0)
                }
            )
            
            if not created:
                node.is_synced = status.get('is_synced', False)
                node.current_block_height = status.get('block_height', 0)
                node.save()
            
            return status
        
        except Exception as e:
            logger.error(f"Failed to get blockchain status for {blockchain}: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def get_blockchain_status_sync(blockchain: str) -> Dict[str, Any]:
        """
        Get blockchain node status (synchronous version for metrics collection)
        
        Args:
            blockchain: Blockchain name
            
        Returns:
            Blockchain status dictionary
        """
        try:
            # Get cached status from database first
            try:
                node = BlockchainNode.objects.get(blockchain=blockchain)
                return {
                    'blockchain': blockchain,
                    'is_synced': node.is_synced,
                    'current_block': node.current_block_height,
                    'highest_block': node.current_block_height,  # Simplified for sync version
                    'peer_count': 0,  # Would need separate tracking
                    'last_block_time': timezone.now().timestamp(),
                    'network': node.network
                }
            except BlockchainNode.DoesNotExist:
                # Return default status if no record exists
                return {
                    'blockchain': blockchain,
                    'is_synced': False,
                    'current_block': 0,
                    'highest_block': 0,
                    'peer_count': 0,
                    'last_block_time': timezone.now().timestamp(),
                    'network': 'unknown'
                }
        
        except Exception as e:
            logger.error(f"Failed to get blockchain status for {blockchain}: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    async def health_check() -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all blockchain adapters
        
        Returns:
            Health status for all blockchains
        """
        return await BlockchainAdapterFactory.health_check()
    
    @staticmethod
    def get_user_addresses(user: User, blockchain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all addresses for a user
        
        Args:
            user: User instance
            blockchain: Optional blockchain filter
            
        Returns:
            List of address dictionaries
        """
        queryset = BlockchainAddress.objects.filter(user=user, is_active=True)
        
        if blockchain:
            queryset = queryset.filter(blockchain=blockchain)
        
        return [
            {
                'blockchain': addr.blockchain,
                'address': addr.address,
                'created_at': addr.created_at
            }
            for addr in queryset
        ]
    
    @staticmethod
    def get_user_transactions(user: User, blockchain: Optional[str] = None, 
                            limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get transaction history for a user
        
        Args:
            user: User instance
            blockchain: Optional blockchain filter
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries
        """
        queryset = BlockchainTransaction.objects.filter(user=user)
        
        if blockchain:
            queryset = queryset.filter(blockchain=blockchain)
        
        queryset = queryset.order_by('-created_at')[:limit]
        
        return [
            {
                'blockchain': tx.blockchain,
                'transaction_hash': tx.transaction_hash,
                'from_address': tx.from_address,
                'to_address': tx.to_address,
                'amount': str(tx.amount),
                'fee': str(tx.fee) if tx.fee else None,
                'status': tx.status,
                'confirmations': tx.confirmations,
                'created_at': tx.created_at,
                'confirmed_at': tx.confirmed_at
            }
            for tx in queryset
        ]