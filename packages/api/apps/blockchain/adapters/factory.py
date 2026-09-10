"""
Blockchain adapter factory for creating and managing adapter instances
"""

from typing import Dict, Optional
from django.core.cache import cache
import logging

from .base import BlockchainAdapterInterface
from .bitcoin import BitcoinAdapter
from .ethereum import EthereumAdapter
from .cardano import CardanoAdapter
from .polkadot import PolkadotAdapter
from ..config import BlockchainConfig

logger = logging.getLogger(__name__)


class BlockchainAdapterFactory:
    """
    Factory class for creating and managing blockchain adapter instances
    """
    
    _adapters: Dict[str, BlockchainAdapterInterface] = {}
    
    ADAPTER_CLASSES = {
        'bitcoin': BitcoinAdapter,
        'ethereum': EthereumAdapter,
        'cardano': CardanoAdapter,
        'polkadot': PolkadotAdapter,
    }
    
    @classmethod
    def get_adapter(cls, blockchain: str) -> BlockchainAdapterInterface:
        """
        Get or create a blockchain adapter instance
        
        Args:
            blockchain: Name of the blockchain
            
        Returns:
            Blockchain adapter instance
            
        Raises:
            ValueError: If blockchain is not supported
        """
        if blockchain not in cls.ADAPTER_CLASSES:
            raise ValueError(f"Unsupported blockchain: {blockchain}")
        
        # Return cached adapter if exists
        if blockchain in cls._adapters:
            return cls._adapters[blockchain]
        
        # Create new adapter instance
        try:
            config = BlockchainConfig.get_config(blockchain)
            adapter_class = cls.ADAPTER_CLASSES[blockchain]
            adapter = adapter_class(config)
            
            # Cache the adapter
            cls._adapters[blockchain] = adapter
            
            logger.info(f"Created {blockchain} adapter with config: {config['network']}")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create {blockchain} adapter: {str(e)}")
            raise
    
    @classmethod
    def get_all_adapters(cls) -> Dict[str, BlockchainAdapterInterface]:
        """
        Get all available blockchain adapters
        
        Returns:
            Dictionary of blockchain name to adapter instance
        """
        adapters = {}
        for blockchain in cls.ADAPTER_CLASSES.keys():
            try:
                adapters[blockchain] = cls.get_adapter(blockchain)
            except Exception as e:
                logger.warning(f"Failed to initialize {blockchain} adapter: {str(e)}")
        
        return adapters
    
    @classmethod
    def clear_cache(cls):
        """Clear cached adapter instances"""
        cls._adapters.clear()
        logger.info("Cleared blockchain adapter cache")
    
    @classmethod
    def is_supported(cls, blockchain: str) -> bool:
        """
        Check if a blockchain is supported
        
        Args:
            blockchain: Name of the blockchain
            
        Returns:
            True if supported, False otherwise
        """
        return blockchain in cls.ADAPTER_CLASSES
    
    @classmethod
    def get_supported_blockchains(cls) -> list:
        """
        Get list of supported blockchain names
        
        Returns:
            List of supported blockchain names
        """
        return list(cls.ADAPTER_CLASSES.keys())
    
    @classmethod
    async def health_check(cls) -> Dict[str, Dict[str, any]]:
        """
        Perform health check on all adapters
        
        Returns:
            Dictionary with health status for each blockchain
        """
        health_status = {}
        
        for blockchain in cls.ADAPTER_CLASSES.keys():
            try:
                adapter = cls.get_adapter(blockchain)
                status = await adapter.get_network_status()
                health_status[blockchain] = {
                    'status': 'healthy',
                    'details': status
                }
            except Exception as e:
                health_status[blockchain] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return health_status