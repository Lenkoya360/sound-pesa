"""
Cardano blockchain adapter implementation
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List
from decimal import Decimal
import re

from .base import BaseBlockchainAdapter


class CardanoAdapter(BaseBlockchainAdapter):
    """
    Cardano blockchain adapter for Cardano node integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.socket_path = config.get('socket_path')
        self.protocol_parameters_url = config.get('protocol_parameters_url')
        
        # Cardano constants
        self.LOVELACE_PER_ADA = Decimal('1000000')  # 1 ADA = 1,000,000 lovelace
    
    async def _rpc_call(self, method: str, params: Dict[str, Any] = None) -> Any:
        """
        Make HTTP call to Cardano node REST API
        
        Args:
            method: API endpoint
            params: Request parameters
            
        Returns:
            API response
        """
        if params is None:
            params = {}
        
        url = f"{self.rpc_url}/{method}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        raise Exception(f"API call failed with status {response.status}")
                    
                    return await response.json()
        
        except Exception as e:
            self.log_error('rpc_call', e, method=method, params=params)
            raise
    
    def validate_address(self, address: str) -> bool:
        """
        Validate Cardano address format
        
        Args:
            address: Cardano address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not address or not isinstance(address, str):
            return False
        
        # Cardano addresses can be:
        # - Byron era addresses (start with Ae2, DdzFF)
        # - Shelley era addresses (start with addr1)
        # - Stake addresses (start with stake1)
        
        byron_pattern = r'^(Ae2|DdzFF)[1-9A-HJ-NP-Za-km-z]{50,104}$'
        shelley_pattern = r'^addr1[a-z0-9]{53,}$'
        stake_pattern = r'^stake1[a-z0-9]{53,}$'
        
        return (self.validate_address_format(address, byron_pattern) or
                self.validate_address_format(address, shelley_pattern) or
                self.validate_address_format(address, stake_pattern))
    
    def _lovelace_to_ada(self, lovelace: str) -> str:
        """Convert lovelace to ADA"""
        lovelace_decimal = Decimal(lovelace)
        ada_decimal = lovelace_decimal / self.LOVELACE_PER_ADA
        return str(ada_decimal)
    
    def _ada_to_lovelace(self, ada: str) -> str:
        """Convert ADA to lovelace"""
        ada_decimal = Decimal(ada)
        lovelace_decimal = ada_decimal * self.LOVELACE_PER_ADA
        return str(int(lovelace_decimal))
    
    async def get_balance(self, address: str) -> str:
        """
        Get Cardano balance for address
        
        Args:
            address: Cardano address
            
        Returns:
            Balance in ADA as string
        """
        try:
            # Get UTXOs for the address
            utxos = await self._rpc_call(f'addresses/{address}/utxos')
            
            total_lovelace = Decimal('0')
            for utxo in utxos:
                for amount in utxo.get('amount', []):
                    if amount.get('unit') == 'lovelace':
                        total_lovelace += Decimal(amount.get('quantity', '0'))
            
            return self._lovelace_to_ada(str(total_lovelace))
        
        except Exception as e:
            self.log_error('get_balance', e, address=address)
            return '0'
    
    async def estimate_fee(self, from_address: str, to_address: str, amount: str) -> str:
        """
        Estimate Cardano transaction fee
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in ADA
            
        Returns:
            Estimated fee in ADA
        """
        try:
            # Get protocol parameters for fee calculation
            protocol_params = await self._rpc_call('epochs/latest/parameters')
            
            # Basic fee calculation (simplified)
            min_fee_a = protocol_params.get('min_fee_a', 44)  # Linear fee coefficient
            min_fee_b = protocol_params.get('min_fee_b', 155381)  # Constant fee
            
            # Estimate transaction size (simplified)
            # Actual implementation would build the transaction and calculate exact size
            estimated_size = 300  # bytes
            
            fee_lovelace = min_fee_a * estimated_size + min_fee_b
            return self._lovelace_to_ada(str(fee_lovelace))
        
        except Exception as e:
            self.log_error('estimate_fee', e, from_address=from_address, to_address=to_address)
            return '0.2'  # Default fee estimate in ADA
    
    async def send_transaction(self, from_address: str, to_address: str, 
                             amount: str, private_key: str) -> str:
        """
        Send Cardano transaction
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in ADA
            private_key: Private key for signing
            
        Returns:
            Transaction hash
        """
        try:
            # Note: This is a placeholder implementation
            # Real Cardano transaction creation requires:
            # 1. Building transaction with cardano-cli or similar library
            # 2. Signing with private key
            # 3. Submitting to network
            
            # For now, this is a mock implementation
            raise NotImplementedError("Cardano transaction sending not fully implemented")
        
        except Exception as e:
            self.log_error('send_transaction', e, 
                         from_address=from_address, to_address=to_address, amount=amount)
            raise
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get Cardano transaction details
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details
        """
        try:
            tx_info = await self._rpc_call(f'txs/{tx_hash}')
            
            # Get current block height for confirmations
            current_block = await self.get_block_height()
            tx_block = tx_info.get('block_height', 0)
            confirmations = current_block - tx_block + 1 if tx_block > 0 else 0
            
            # Calculate total output amount
            total_output = Decimal('0')
            for output in tx_info.get('outputs', []):
                for amount in output.get('amount', []):
                    if amount.get('unit') == 'lovelace':
                        total_output += Decimal(amount.get('quantity', '0'))
            
            return {
                'hash': tx_hash,
                'block': tx_info.get('block'),
                'block_height': tx_info.get('block_height'),
                'slot': tx_info.get('slot'),
                'index': tx_info.get('index'),
                'fee': self._lovelace_to_ada(str(tx_info.get('fees', '0'))),
                'size': tx_info.get('size'),
                'confirmations': confirmations,
                'inputs': tx_info.get('inputs', []),
                'outputs': tx_info.get('outputs', []),
                'total_output': self._lovelace_to_ada(str(total_output))
            }
        
        except Exception as e:
            self.log_error('get_transaction', e, tx_hash=tx_hash)
            raise
    
    async def get_block_height(self) -> int:
        """
        Get current Cardano block height
        
        Returns:
            Current block height
        """
        try:
            block_info = await self._rpc_call('blocks/latest')
            return block_info.get('height', 0)
        except Exception as e:
            self.log_error('get_block_height', e)
            return 0
    
    async def is_node_synced(self) -> bool:
        """
        Check if Cardano node is synchronized
        
        Returns:
            True if synced, False otherwise
        """
        try:
            network_info = await self._rpc_call('network')
            sync_progress = network_info.get('sync_progress', '0%')
            return sync_progress == '100%'
        except Exception as e:
            self.log_error('is_node_synced', e)
            return False
    
    async def generate_address(self, private_key: Optional[str] = None) -> Dict[str, str]:
        """
        Generate new Cardano address and private key
        
        Args:
            private_key: Optional existing private key
            
        Returns:
            Dictionary with 'address' and 'private_key'
        """
        try:
            # Note: This is a placeholder implementation
            # Real Cardano address generation requires:
            # 1. Generating or using existing private key
            # 2. Deriving public key
            # 3. Creating payment and stake key hashes
            # 4. Building address from key hashes
            
            raise NotImplementedError("Cardano address generation not fully implemented")
        
        except Exception as e:
            self.log_error('generate_address', e)
            raise
    
    async def get_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Get unspent transaction outputs for address
        
        Args:
            address: Cardano address
            
        Returns:
            List of UTXO dictionaries
        """
        try:
            return await self._rpc_call(f'addresses/{address}/utxos')
        except Exception as e:
            self.log_error('get_utxos', e, address=address)
            return []
    
    async def get_protocol_parameters(self) -> Dict[str, Any]:
        """
        Get current protocol parameters
        
        Returns:
            Protocol parameters dictionary
        """
        try:
            return await self._rpc_call('epochs/latest/parameters')
        except Exception as e:
            self.log_error('get_protocol_parameters', e)
            return {}
    
    async def submit_transaction(self, signed_tx: str) -> str:
        """
        Submit a signed transaction to the network
        
        Args:
            signed_tx: Signed transaction in CBOR format
            
        Returns:
            Transaction hash
        """
        try:
            # Note: This would require proper Cardano transaction submission
            # For now, this is a placeholder
            raise NotImplementedError("Cardano transaction submission not fully implemented")
        
        except Exception as e:
            self.log_error('submit_transaction', e, signed_tx=signed_tx[:20])
            raise
    
    async def get_epoch_info(self) -> Dict[str, Any]:
        """
        Get current epoch information
        
        Returns:
            Epoch information dictionary
        """
        try:
            return await self._rpc_call('epochs/latest')
        except Exception as e:
            self.log_error('get_epoch_info', e)
            return {}
    
    async def get_stake_pool_info(self, pool_id: str) -> Dict[str, Any]:
        """
        Get stake pool information
        
        Args:
            pool_id: Stake pool ID
            
        Returns:
            Stake pool information
        """
        try:
            return await self._rpc_call(f'pools/{pool_id}')
        except Exception as e:
            self.log_error('get_stake_pool_info', e, pool_id=pool_id)
            return {}
    
    async def get_address_transactions(self, address: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get transaction history for an address
        
        Args:
            address: Cardano address
            count: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries
        """
        try:
            return await self._rpc_call(f'addresses/{address}/transactions', {'count': count})
        except Exception as e:
            self.log_error('get_address_transactions', e, address=address)
            return []
    
    async def monitor_transaction_status(self, tx_hash: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Monitor transaction status until confirmed or timeout
        
        Args:
            tx_hash: Transaction hash to monitor
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            Final transaction status
        """
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                tx_info = await self.get_transaction(tx_hash)
                
                # Check if transaction is confirmed
                if tx_info.get('confirmations', 0) >= self.confirmations_required:
                    return {
                        'status': 'confirmed',
                        'confirmations': tx_info.get('confirmations'),
                        'block_height': tx_info.get('block_height')
                    }
                
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > max_wait_time:
                    return {
                        'status': 'timeout',
                        'confirmations': tx_info.get('confirmations', 0)
                    }
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                self.log_error('monitor_transaction_status', e, tx_hash=tx_hash)
                return {
                    'status': 'error',
                    'error': str(e)
                }