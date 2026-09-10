"""
Base blockchain adapter interface and implementation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
import re
import logging

logger = logging.getLogger(__name__)


class BlockchainAdapterInterface(ABC):
    """
    Abstract interface for blockchain adapters
    Defines common methods that all blockchain adapters must implement
    """
    
    @abstractmethod
    async def get_balance(self, address: str) -> str:
        """
        Get the balance for a given address
        
        Args:
            address: The blockchain address to check
            
        Returns:
            Balance as string for precise decimal handling
        """
        pass
    
    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """
        Validate if an address is valid for this blockchain
        
        Args:
            address: The address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def estimate_fee(self, from_address: str, to_address: str, amount: str) -> str:
        """
        Estimate transaction fee for a transfer
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to transfer
            
        Returns:
            Estimated fee as string
        """
        pass
    
    @abstractmethod
    async def send_transaction(self, from_address: str, to_address: str, 
                             amount: str, private_key: str) -> str:
        """
        Send a transaction on the blockchain
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to transfer
            private_key: Private key for signing
            
        Returns:
            Transaction hash
        """
        pass
    
    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction details by hash
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details dictionary
        """
        pass
    
    @abstractmethod
    async def get_block_height(self) -> int:
        """
        Get current block height
        
        Returns:
            Current block height
        """
        pass
    
    @abstractmethod
    async def is_node_synced(self) -> bool:
        """
        Check if the blockchain node is fully synchronized
        
        Returns:
            True if synced, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_address(self, private_key: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a new address and private key pair
        
        Args:
            private_key: Optional existing private key
            
        Returns:
            Dictionary with 'address' and 'private_key'
        """
        pass


class BaseBlockchainAdapter(BlockchainAdapterInterface):
    """
    Base implementation providing common functionality for blockchain adapters
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adapter with configuration
        
        Args:
            config: Blockchain-specific configuration
        """
        self.config = config
        self.blockchain_name = config.get('name', 'unknown')
        self.network = config.get('network', 'mainnet')
        self.rpc_url = config.get('rpc_url')
        self.confirmations_required = config.get('confirmations_required', 6)
        self.min_amount = Decimal(config.get('min_transaction_amount', '0.00000001'))
        self.max_amount = Decimal(config.get('max_transaction_amount', '1000000'))
        
        if not self.rpc_url:
            raise ValueError(f"RPC URL is required for {self.blockchain_name} adapter")
    
    def validate_amount(self, amount: str) -> bool:
        """
        Validate transaction amount is within acceptable range
        
        Args:
            amount: Amount to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            amount_decimal = Decimal(amount)
            return self.min_amount <= amount_decimal <= self.max_amount
        except (ValueError, TypeError, InvalidOperation):
            return False
    
    def validate_address_format(self, address: str, pattern: str) -> bool:
        """
        Validate address format using regex pattern
        
        Args:
            address: Address to validate
            pattern: Regex pattern for validation
            
        Returns:
            True if valid format, False otherwise
        """
        if not address or not isinstance(address, str):
            return False
        
        return bool(re.match(pattern, address))
    
    def format_amount(self, amount: str, decimals: int = 8) -> str:
        """
        Format amount to specified decimal places
        
        Args:
            amount: Amount to format
            decimals: Number of decimal places
            
        Returns:
            Formatted amount string
        """
        try:
            amount_decimal = Decimal(amount)
            return f"{amount_decimal:.{decimals}f}"
        except (ValueError, TypeError, InvalidOperation):
            raise ValueError(f"Invalid amount format: {amount}")
    
    def log_transaction(self, tx_hash: str, from_addr: str, to_addr: str, amount: str):
        """
        Log transaction details for audit purposes
        
        Args:
            tx_hash: Transaction hash
            from_addr: Source address
            to_addr: Destination address
            amount: Transaction amount
        """
        logger.info(
            f"Transaction sent on {self.blockchain_name}: "
            f"hash={tx_hash}, from={from_addr}, to={to_addr}, amount={amount}"
        )
    
    def log_error(self, operation: str, error: Exception, **kwargs):
        """
        Log error with context information
        
        Args:
            operation: Operation that failed
            error: Exception that occurred
            **kwargs: Additional context
        """
        context = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.error(
            f"Error in {self.blockchain_name} {operation}: {str(error)} "
            f"({context})"
        )
    
    async def get_network_status(self) -> Dict[str, Any]:
        """
        Get general network status information
        
        Returns:
            Network status dictionary
        """
        try:
            block_height = await self.get_block_height()
            is_synced = await self.is_node_synced()
            
            return {
                'blockchain': self.blockchain_name,
                'network': self.network,
                'block_height': block_height,
                'is_synced': is_synced,
                'rpc_url': self.rpc_url
            }
        except Exception as e:
            self.log_error('get_network_status', e)
            return {
                'blockchain': self.blockchain_name,
                'network': self.network,
                'error': str(e)
            }