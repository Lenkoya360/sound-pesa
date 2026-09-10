"""
Blockchain configuration management
"""

import os
from typing import Dict, Any
from django.conf import settings


class BlockchainConfig:
    """
    Centralized blockchain configuration management
    """
    
    @staticmethod
    def get_bitcoin_config() -> Dict[str, Any]:
        """Get Bitcoin blockchain configuration"""
        return {
            'name': 'bitcoin',
            'network': os.getenv('BITCOIN_NETWORK', 'testnet'),
            'rpc_url': os.getenv('BITCOIN_RPC_URL', 'http://bitcoin-core:18332'),
            'rpc_user': os.getenv('BITCOIN_RPC_USER', 'bitcoin'),
            'rpc_password': os.getenv('BITCOIN_RPC_PASSWORD', 'password'),
            'confirmations_required': int(os.getenv('BITCOIN_CONFIRMATIONS', '6')),
            'min_transaction_amount': os.getenv('BITCOIN_MIN_AMOUNT', '0.00000546'),  # Dust limit
            'max_transaction_amount': os.getenv('BITCOIN_MAX_AMOUNT', '21000000'),
            'fee_rate_per_byte': int(os.getenv('BITCOIN_FEE_RATE', '10')),  # satoshis per byte
        }
    
    @staticmethod
    def get_ethereum_config() -> Dict[str, Any]:
        """Get Ethereum blockchain configuration"""
        return {
            'name': 'ethereum',
            'network': os.getenv('ETHEREUM_NETWORK', 'goerli'),
            'rpc_url': os.getenv('ETHEREUM_RPC_URL', 'http://geth:8545'),
            'chain_id': int(os.getenv('ETHEREUM_CHAIN_ID', '5')),  # Goerli testnet
            'confirmations_required': int(os.getenv('ETHEREUM_CONFIRMATIONS', '12')),
            'min_transaction_amount': os.getenv('ETHEREUM_MIN_AMOUNT', '0.000000000000000001'),  # 1 wei
            'max_transaction_amount': os.getenv('ETHEREUM_MAX_AMOUNT', '1000000'),
            'gas_limit': int(os.getenv('ETHEREUM_GAS_LIMIT', '21000')),
            'gas_price_gwei': int(os.getenv('ETHEREUM_GAS_PRICE', '20')),
        }
    
    @staticmethod
    def get_cardano_config() -> Dict[str, Any]:
        """Get Cardano blockchain configuration"""
        return {
            'name': 'cardano',
            'network': os.getenv('CARDANO_NETWORK', 'testnet'),
            'rpc_url': os.getenv('CARDANO_RPC_URL', 'http://cardano-node:3001'),
            'socket_path': os.getenv('CARDANO_SOCKET_PATH', '/opt/cardano/cnode/sockets/node0.socket'),
            'confirmations_required': int(os.getenv('CARDANO_CONFIRMATIONS', '5')),
            'min_transaction_amount': os.getenv('CARDANO_MIN_AMOUNT', '1000000'),  # 1 ADA in lovelace
            'max_transaction_amount': os.getenv('CARDANO_MAX_AMOUNT', '45000000000'),  # 45B ADA
            'protocol_parameters_url': os.getenv('CARDANO_PROTOCOL_PARAMS_URL', 'http://cardano-node:3001/protocol-parameters'),
        }
    
    @staticmethod
    def get_polkadot_config() -> Dict[str, Any]:
        """Get Polkadot blockchain configuration"""
        return {
            'name': 'polkadot',
            'network': os.getenv('POLKADOT_NETWORK', 'westend'),
            'rpc_url': os.getenv('POLKADOT_RPC_URL', 'ws://polkadot:9944'),
            'confirmations_required': int(os.getenv('POLKADOT_CONFIRMATIONS', '2')),
            'min_transaction_amount': os.getenv('POLKADOT_MIN_AMOUNT', '10000000000'),  # 1 DOT in planck
            'max_transaction_amount': os.getenv('POLKADOT_MAX_AMOUNT', '1000000000000000000'),  # 1B DOT
            'existential_deposit': os.getenv('POLKADOT_EXISTENTIAL_DEPOSIT', '10000000000'),  # 1 DOT
        }
    
    @staticmethod
    def get_all_configs() -> Dict[str, Dict[str, Any]]:
        """Get all blockchain configurations"""
        return {
            'bitcoin': BlockchainConfig.get_bitcoin_config(),
            'ethereum': BlockchainConfig.get_ethereum_config(),
            'cardano': BlockchainConfig.get_cardano_config(),
            'polkadot': BlockchainConfig.get_polkadot_config(),
        }
    
    @staticmethod
    def get_config(blockchain: str) -> Dict[str, Any]:
        """
        Get configuration for a specific blockchain
        
        Args:
            blockchain: Name of the blockchain
            
        Returns:
            Configuration dictionary
            
        Raises:
            ValueError: If blockchain is not supported
        """
        configs = BlockchainConfig.get_all_configs()
        if blockchain not in configs:
            raise ValueError(f"Unsupported blockchain: {blockchain}")
        
        return configs[blockchain]
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        Validate blockchain configuration
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'name', 'network', 'rpc_url', 'confirmations_required',
            'min_transaction_amount', 'max_transaction_amount'
        ]
        
        for field in required_fields:
            if field not in config:
                return False
        
        # Validate numeric fields
        try:
            int(config['confirmations_required'])
            float(config['min_transaction_amount'])
            float(config['max_transaction_amount'])
        except (ValueError, TypeError):
            return False
        
        return True