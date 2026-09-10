"""
Tests for blockchain integration layer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase

from .adapters import BlockchainAdapterFactory
from .adapters.base import BaseBlockchainAdapter
from .config import BlockchainConfig
from .services import BlockchainService


class _ConcreteTestAdapter(BaseBlockchainAdapter):
    """Minimum concrete subclass used to exercise base-class helpers that are
    not overridden by real adapters."""
    async def estimate_fee(self, from_address, to_address, amount):
        return '0.0001'
    async def generate_address(self, private_key=None):
        return {'address': 'addr', 'private_key': 'key'}
    async def get_balance(self, address):
        return '0'
    async def get_block_height(self):
        return 0
    async def get_transaction(self, tx_hash):
        return {}
    async def is_node_synced(self):
        return False
    async def send_transaction(self, from_address, to_address, amount, private_key):
        return 'txhash'
    def validate_address(self, address):
        return False


class BlockchainConfigTest(TestCase):
    """Test blockchain configuration management"""
    
    def test_get_bitcoin_config(self):
        """Test Bitcoin configuration retrieval"""
        config = BlockchainConfig.get_bitcoin_config()
        
        self.assertIn('name', config)
        self.assertEqual(config['name'], 'bitcoin')
        self.assertIn('rpc_url', config)
        self.assertIn('confirmations_required', config)
    
    def test_get_ethereum_config(self):
        """Test Ethereum configuration retrieval"""
        config = BlockchainConfig.get_ethereum_config()
        
        self.assertIn('name', config)
        self.assertEqual(config['name'], 'ethereum')
        self.assertIn('rpc_url', config)
        self.assertIn('chain_id', config)
    
    def test_get_all_configs(self):
        """Test getting all blockchain configurations"""
        configs = BlockchainConfig.get_all_configs()
        
        self.assertIn('bitcoin', configs)
        self.assertIn('ethereum', configs)
        self.assertIn('cardano', configs)
        self.assertIn('polkadot', configs)
    
    def test_validate_config(self):
        """Test configuration validation"""
        valid_config = {
            'name': 'bitcoin',
            'network': 'testnet',
            'rpc_url': 'http://localhost:18332',
            'confirmations_required': 6,
            'min_transaction_amount': '0.00000546',
            'max_transaction_amount': '21000000'
        }
        
        self.assertTrue(BlockchainConfig.validate_config(valid_config))
        
        # Test invalid config
        invalid_config = valid_config.copy()
        del invalid_config['rpc_url']
        
        self.assertFalse(BlockchainConfig.validate_config(invalid_config))


class BlockchainAdapterFactoryTest(TestCase):
    """Test blockchain adapter factory"""
    
    def test_is_supported(self):
        """Test blockchain support checking"""
        self.assertTrue(BlockchainAdapterFactory.is_supported('bitcoin'))
        self.assertTrue(BlockchainAdapterFactory.is_supported('ethereum'))
        self.assertTrue(BlockchainAdapterFactory.is_supported('cardano'))
        self.assertTrue(BlockchainAdapterFactory.is_supported('polkadot'))
        self.assertFalse(BlockchainAdapterFactory.is_supported('unsupported'))
    
    def test_get_supported_blockchains(self):
        """Test getting supported blockchain list"""
        supported = BlockchainAdapterFactory.get_supported_blockchains()
        
        self.assertIn('bitcoin', supported)
        self.assertIn('ethereum', supported)
        self.assertIn('cardano', supported)
        self.assertIn('polkadot', supported)
    
    def test_get_adapter(self):
        """Test adapter creation"""
        # Clear cache first
        BlockchainAdapterFactory.clear_cache()

        # Swap the registered class with a mock so the factory builds a mock
        mock_adapter_class = MagicMock()
        mock_instance = AsyncMock()
        mock_adapter_class.return_value = mock_instance
        original = BlockchainAdapterFactory.ADAPTER_CLASSES['bitcoin']
        BlockchainAdapterFactory.ADAPTER_CLASSES['bitcoin'] = mock_adapter_class
        try:
            # Get adapter
            adapter = BlockchainAdapterFactory.get_adapter('bitcoin')
        finally:
            BlockchainAdapterFactory.ADAPTER_CLASSES['bitcoin'] = original
            BlockchainAdapterFactory.clear_cache()

        # Verify adapter was created
        self.assertIs(mock_instance, adapter)
        mock_adapter_class.assert_called_once()
    
    def test_get_adapter_unsupported(self):
        """Test getting unsupported adapter raises error"""
        with self.assertRaises(ValueError):
            BlockchainAdapterFactory.get_adapter('unsupported')


class BlockchainAdapterTest(TestCase):
    """Test blockchain adapter base functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'name': 'bitcoin',
            'network': 'testnet',
            'rpc_url': 'http://localhost:18332',
            'confirmations_required': 6,
            'min_transaction_amount': '0.00000546',
            'max_transaction_amount': '21000000'
        }
    
    def test_validate_amount(self):
        """Test amount validation"""
        adapter = _ConcreteTestAdapter(self.config)
        
        # Valid amounts
        self.assertTrue(adapter.validate_amount('1.0'))
        self.assertTrue(adapter.validate_amount('0.1'))
        
        # Invalid amounts
        self.assertFalse(adapter.validate_amount('0'))  # Too small
        self.assertFalse(adapter.validate_amount('99999999'))  # Too large
        self.assertFalse(adapter.validate_amount('invalid'))  # Invalid format
    
    def test_format_amount(self):
        """Test amount formatting"""
        adapter = _ConcreteTestAdapter(self.config)
        
        self.assertEqual(adapter.format_amount('1.23456789', 8), '1.23456789')
        self.assertEqual(adapter.format_amount('1.23456789', 2), '1.23')
        
        with self.assertRaises(ValueError):
            adapter.format_amount('invalid')
    
    def test_validate_address_format(self):
        """Test address format validation"""
        adapter = _ConcreteTestAdapter(self.config)
        
        # Valid format
        self.assertTrue(adapter.validate_address_format('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'))
        
        # Invalid format
        self.assertFalse(adapter.validate_address_format('invalid', r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'))
        self.assertFalse(adapter.validate_address_format('', r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'))
        self.assertFalse(adapter.validate_address_format(None, r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'))


class BitcoinAdapterTest(TestCase):
    """Test Bitcoin adapter functionality"""
    
    def test_validate_address(self):
        """Test Bitcoin address validation"""
        from .adapters.bitcoin import BitcoinAdapter
        
        config = BlockchainConfig.get_bitcoin_config()
        adapter = BitcoinAdapter(config)
        
        # Valid addresses
        self.assertTrue(adapter.validate_address('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'))  # P2PKH
        self.assertTrue(adapter.validate_address('3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy'))  # P2SH
        self.assertTrue(adapter.validate_address('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4'))  # Bech32
        
        # Invalid addresses
        self.assertFalse(adapter.validate_address('invalid'))
        self.assertFalse(adapter.validate_address(''))
        self.assertFalse(adapter.validate_address(None))
    
    def test_satoshis_conversion(self):
        """Test satoshis to BTC conversion"""
        from .adapters.bitcoin import BitcoinAdapter
        
        config = BlockchainConfig.get_bitcoin_config()
        adapter = BitcoinAdapter(config)
        
        self.assertEqual(adapter.satoshis_to_btc(100000000), '1.00000000')
        self.assertEqual(adapter.satoshis_to_btc(50000000), '0.50000000')
        self.assertEqual(adapter.btc_to_satoshis('1.0'), 100000000)
        self.assertEqual(adapter.btc_to_satoshis('0.5'), 50000000)


class EthereumAdapterTest(TestCase):
    """Test Ethereum adapter functionality"""
    
    def test_validate_address(self):
        """Test Ethereum address validation"""
        from .adapters.ethereum import EthereumAdapter
        
        config = BlockchainConfig.get_ethereum_config()
        adapter = EthereumAdapter(config)
        
        # Valid addresses
        self.assertTrue(adapter.validate_address('0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6'))
        self.assertTrue(adapter.validate_address('0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe'))
        
        # Invalid addresses
        self.assertFalse(adapter.validate_address('invalid'))
        self.assertFalse(adapter.validate_address('0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b'))  # Too short
        self.assertFalse(adapter.validate_address('742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6'))  # No 0x prefix
    
    def test_wei_conversion(self):
        """Test Wei to ETH conversion"""
        from .adapters.ethereum import EthereumAdapter
        
        config = BlockchainConfig.get_ethereum_config()
        adapter = EthereumAdapter(config)
        
        self.assertEqual(adapter._wei_to_eth('1000000000000000000'), '1')
        self.assertEqual(adapter._wei_to_eth('500000000000000000'), '0.5')
        self.assertEqual(adapter._eth_to_wei('1'), '0xde0b6b3a7640000')
        self.assertEqual(adapter._eth_to_wei('0.5'), '0x6f05b59d3b20000')


# Note: Async tests would require pytest-asyncio for proper testing
# This is a basic test structure to verify the integration layer works