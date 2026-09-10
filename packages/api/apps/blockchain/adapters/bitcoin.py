"""
Bitcoin blockchain adapter implementation
"""

import asyncio
import json
import aiohttp
import base64
from typing import Dict, Any, Optional, List
from decimal import Decimal
import hashlib
import secrets

from .base import BaseBlockchainAdapter


class BitcoinAdapter(BaseBlockchainAdapter):
    """
    Bitcoin blockchain adapter for Core RPC integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rpc_user = config.get('rpc_user', 'bitcoin')
        self.rpc_password = config.get('rpc_password', 'password')
        self.fee_rate_per_byte = config.get('fee_rate_per_byte', 10)
        
        # Create auth header for RPC calls
        auth_string = f"{self.rpc_user}:{self.rpc_password}"
        auth_bytes = auth_string.encode('ascii')
        self.auth_header = base64.b64encode(auth_bytes).decode('ascii')
    
    async def _rpc_call(self, method: str, params: List[Any] = None) -> Any:
        """
        Make RPC call to Bitcoin Core node
        
        Args:
            method: RPC method name
            params: Method parameters
            
        Returns:
            RPC response result
        """
        if params is None:
            params = []
        
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self.auth_header}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        raise Exception(f"RPC call failed with status {response.status}")
                    
                    result = await response.json()
                    
                    if 'error' in result and result['error']:
                        raise Exception(f"RPC error: {result['error']}")
                    
                    return result.get('result')
        
        except Exception as e:
            self.log_error('rpc_call', e, method=method, params=params)
            raise
    
    def validate_address(self, address: str) -> bool:
        """
        Validate Bitcoin address format
        
        Args:
            address: Bitcoin address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not address or not isinstance(address, str):
            return False
        
        # Legacy P2PKH addresses (start with 1)
        if address.startswith('1'):
            return self.validate_address_format(address, r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$')
        
        # P2SH addresses (start with 3)
        elif address.startswith('3'):
            return self.validate_address_format(address, r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$')
        
        # Bech32 addresses (start with bc1 for mainnet, tb1 for testnet)
        elif address.startswith('bc1') or address.startswith('tb1'):
            return self.validate_address_format(address, r'^(bc1|tb1)[a-z0-9]{39,59}$')
        
        return False
    
    async def get_balance(self, address: str) -> str:
        """
        Get Bitcoin balance for address
        
        Args:
            address: Bitcoin address
            
        Returns:
            Balance in BTC as string
        """
        try:
            # Import address to wallet if not already imported
            await self._rpc_call('importaddress', [address, '', False])
            
            # Get unspent outputs for address
            utxos = await self._rpc_call('listunspent', [0, 9999999, [address]])
            
            total_balance = Decimal('0')
            for utxo in utxos:
                total_balance += Decimal(str(utxo['amount']))
            
            return str(total_balance)
        
        except Exception as e:
            self.log_error('get_balance', e, address=address)
            return '0'
    
    async def estimate_fee(self, from_address: str, to_address: str, amount: str) -> str:
        """
        Estimate Bitcoin transaction fee
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in BTC
            
        Returns:
            Estimated fee in BTC
        """
        try:
            # Get UTXOs for the from_address
            utxos = await self._rpc_call('listunspent', [0, 9999999, [from_address]])
            
            if not utxos:
                raise Exception("No UTXOs available for transaction")
            
            # Simple fee estimation based on transaction size
            # Typical transaction: 1 input + 2 outputs = ~250 bytes
            input_count = len(utxos)
            output_count = 2  # recipient + change
            
            estimated_size = 10 + (input_count * 148) + (output_count * 34)
            fee_satoshis = estimated_size * self.fee_rate_per_byte
            fee_btc = Decimal(fee_satoshis) / Decimal('100000000')
            
            return str(fee_btc)
        
        except Exception as e:
            self.log_error('estimate_fee', e, from_address=from_address, to_address=to_address)
            return '0.0001'  # Default fee
    
    async def send_transaction(self, from_address: str, to_address: str, 
                             amount: str, private_key: str) -> str:
        """
        Send Bitcoin transaction
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in BTC
            private_key: Private key for signing (WIF format)
            
        Returns:
            Transaction hash
        """
        try:
            # Import private key temporarily
            await self._rpc_call('importprivkey', [private_key, '', False])
            
            # Create and send transaction
            tx_hash = await self._rpc_call('sendtoaddress', [to_address, float(amount)])
            
            self.log_transaction(tx_hash, from_address, to_address, amount)
            return tx_hash
        
        except Exception as e:
            self.log_error('send_transaction', e, 
                         from_address=from_address, to_address=to_address, amount=amount)
            raise
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get Bitcoin transaction details
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details
        """
        try:
            tx_info = await self._rpc_call('gettransaction', [tx_hash])
            return {
                'hash': tx_hash,
                'confirmations': tx_info.get('confirmations', 0),
                'amount': str(tx_info.get('amount', 0)),
                'fee': str(abs(tx_info.get('fee', 0))),
                'time': tx_info.get('time'),
                'blocktime': tx_info.get('blocktime'),
                'blockhash': tx_info.get('blockhash'),
                'details': tx_info.get('details', [])
            }
        
        except Exception as e:
            self.log_error('get_transaction', e, tx_hash=tx_hash)
            raise
    
    async def get_block_height(self) -> int:
        """
        Get current Bitcoin block height
        
        Returns:
            Current block height
        """
        try:
            return await self._rpc_call('getblockcount')
        except Exception as e:
            self.log_error('get_block_height', e)
            return 0
    
    async def is_node_synced(self) -> bool:
        """
        Check if Bitcoin node is synchronized
        
        Returns:
            True if synced, False otherwise
        """
        try:
            blockchain_info = await self._rpc_call('getblockchaininfo')
            return blockchain_info.get('initialblockdownload', True) == False
        except Exception as e:
            self.log_error('is_node_synced', e)
            return False
    
    async def generate_address(self, private_key: Optional[str] = None) -> Dict[str, str]:
        """
        Generate new Bitcoin address and private key
        
        Args:
            private_key: Optional existing private key in WIF format
            
        Returns:
            Dictionary with 'address' and 'private_key'
        """
        try:
            if private_key:
                # Import existing private key and get address
                await self._rpc_call('importprivkey', [private_key, '', False])
                address_info = await self._rpc_call('validateaddress', [private_key])
                if not address_info.get('isvalid'):
                    raise Exception("Invalid private key")
                return {
                    'address': address_info['address'],
                    'private_key': private_key
                }
            else:
                # Generate new address
                address = await self._rpc_call('getnewaddress')
                private_key_wif = await self._rpc_call('dumpprivkey', [address])
                
                return {
                    'address': address,
                    'private_key': private_key_wif
                }
        
        except Exception as e:
            self.log_error('generate_address', e)
            raise
    
    async def get_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Get unspent transaction outputs for address
        
        Args:
            address: Bitcoin address
            
        Returns:
            List of UTXO dictionaries
        """
        try:
            return await self._rpc_call('listunspent', [0, 9999999, [address]])
        except Exception as e:
            self.log_error('get_utxos', e, address=address)
            return []
    
    async def create_raw_transaction(self, inputs: List[Dict], outputs: Dict[str, float]) -> str:
        """
        Create a raw Bitcoin transaction
        
        Args:
            inputs: List of input UTXOs
            outputs: Dictionary of output addresses and amounts
            
        Returns:
            Raw transaction hex
        """
        try:
            return await self._rpc_call('createrawtransaction', [inputs, outputs])
        except Exception as e:
            self.log_error('create_raw_transaction', e, inputs=inputs, outputs=outputs)
            raise
    
    async def sign_raw_transaction(self, raw_tx: str, private_keys: List[str]) -> Dict[str, Any]:
        """
        Sign a raw Bitcoin transaction
        
        Args:
            raw_tx: Raw transaction hex
            private_keys: List of private keys for signing
            
        Returns:
            Signed transaction info
        """
        try:
            return await self._rpc_call('signrawtransactionwithkey', [raw_tx, private_keys])
        except Exception as e:
            self.log_error('sign_raw_transaction', e, raw_tx=raw_tx[:20])
            raise
    
    async def broadcast_transaction(self, signed_tx: str) -> str:
        """
        Broadcast a signed transaction to the network
        
        Args:
            signed_tx: Signed transaction hex
            
        Returns:
            Transaction hash
        """
        try:
            return await self._rpc_call('sendrawtransaction', [signed_tx])
        except Exception as e:
            self.log_error('broadcast_transaction', e, signed_tx=signed_tx[:20])
            raise
    
    async def get_mempool_info(self) -> Dict[str, Any]:
        """
        Get mempool information
        
        Returns:
            Mempool statistics
        """
        try:
            return await self._rpc_call('getmempoolinfo')
        except Exception as e:
            self.log_error('get_mempool_info', e)
            return {}
    
    async def estimate_smart_fee(self, conf_target: int = 6) -> Dict[str, Any]:
        """
        Estimate smart fee for confirmation target
        
        Args:
            conf_target: Number of blocks for confirmation target
            
        Returns:
            Fee estimation info
        """
        try:
            return await self._rpc_call('estimatesmartfee', [conf_target])
        except Exception as e:
            self.log_error('estimate_smart_fee', e, conf_target=conf_target)
            return {'feerate': 0.0001}  # Default fallback
    
    def satoshis_to_btc(self, satoshis: int) -> str:
        """Convert satoshis to BTC formatted to 8 decimal places"""
        return self.format_amount(str(Decimal(satoshis) / Decimal('100000000')), 8)
    
    def btc_to_satoshis(self, btc: str) -> int:
        """Convert BTC to satoshis"""
        return int(Decimal(btc) * Decimal('100000000'))