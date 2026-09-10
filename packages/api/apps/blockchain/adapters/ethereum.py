"""
Ethereum blockchain adapter implementation
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List
from decimal import Decimal
import re

from .base import BaseBlockchainAdapter


class EthereumAdapter(BaseBlockchainAdapter):
    """
    Ethereum blockchain adapter for Web3 JSON-RPC integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.chain_id = config.get('chain_id', 1)
        self.gas_limit = config.get('gas_limit', 21000)
        self.gas_price_gwei = config.get('gas_price_gwei', 20)
        
        # Wei conversion constants
        self.WEI_PER_ETH = Decimal('1000000000000000000')  # 10^18
        self.GWEI_PER_ETH = Decimal('1000000000')  # 10^9
    
    async def _rpc_call(self, method: str, params: List[Any] = None) -> Any:
        """
        Make JSON-RPC call to Ethereum node
        
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
        
        headers = {'Content-Type': 'application/json'}
        
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
        Validate Ethereum address format
        
        Args:
            address: Ethereum address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not address or not isinstance(address, str):
            return False
        
        # Ethereum addresses are 42 characters long and start with 0x
        return self.validate_address_format(address, r'^0x[a-fA-F0-9]{40}$')
    
    def _wei_to_eth(self, wei: str) -> str:
        """Convert Wei to ETH"""
        wei_decimal = Decimal(str(int(wei, 16) if wei.startswith('0x') else wei))
        eth_decimal = wei_decimal / self.WEI_PER_ETH
        return str(eth_decimal)
    
    def _eth_to_wei(self, eth: str) -> str:
        """Convert ETH to Wei"""
        eth_decimal = Decimal(eth)
        wei_decimal = eth_decimal * self.WEI_PER_ETH
        return hex(int(wei_decimal))
    
    def _gwei_to_wei(self, gwei: str) -> str:
        """Convert Gwei to Wei"""
        gwei_decimal = Decimal(gwei)
        wei_decimal = gwei_decimal * self.GWEI_PER_ETH
        return hex(int(wei_decimal))
    
    async def get_balance(self, address: str) -> str:
        """
        Get Ethereum balance for address
        
        Args:
            address: Ethereum address
            
        Returns:
            Balance in ETH as string
        """
        try:
            balance_wei = await self._rpc_call('eth_getBalance', [address, 'latest'])
            return self._wei_to_eth(balance_wei)
        
        except Exception as e:
            self.log_error('get_balance', e, address=address)
            return '0'
    
    async def estimate_fee(self, from_address: str, to_address: str, amount: str) -> str:
        """
        Estimate Ethereum transaction fee
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in ETH
            
        Returns:
            Estimated fee in ETH
        """
        try:
            # Get current gas price
            gas_price_wei = await self._rpc_call('eth_gasPrice')
            
            # Estimate gas limit for the transaction
            transaction = {
                'from': from_address,
                'to': to_address,
                'value': self._eth_to_wei(amount)
            }
            
            try:
                gas_limit = await self._rpc_call('eth_estimateGas', [transaction])
                gas_limit_int = int(gas_limit, 16)
            except:
                # Use default gas limit if estimation fails
                gas_limit_int = self.gas_limit
            
            # Calculate fee: gas_limit * gas_price
            gas_price_int = int(gas_price_wei, 16)
            fee_wei = gas_limit_int * gas_price_int
            
            return self._wei_to_eth(str(fee_wei))
        
        except Exception as e:
            self.log_error('estimate_fee', e, from_address=from_address, to_address=to_address)
            # Return default fee estimate
            default_fee_wei = self.gas_limit * (self.gas_price_gwei * 10**9)
            return self._wei_to_eth(str(default_fee_wei))
    
    async def send_transaction(self, from_address: str, to_address: str, 
                             amount: str, private_key: str) -> str:
        """
        Send Ethereum transaction
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in ETH
            private_key: Private key for signing (hex format)
            
        Returns:
            Transaction hash
        """
        try:
            # Get nonce for the from_address
            nonce = await self._rpc_call('eth_getTransactionCount', [from_address, 'pending'])
            
            # Get current gas price
            gas_price = await self._rpc_call('eth_gasPrice')
            
            # Build transaction
            transaction = {
                'from': from_address,
                'to': to_address,
                'value': self._eth_to_wei(amount),
                'gas': hex(self.gas_limit),
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': hex(self.chain_id)
            }
            
            # Note: In a real implementation, you would sign the transaction locally
            # using the private key and then send the signed transaction
            # For now, this is a placeholder that assumes the node has the private key
            tx_hash = await self._rpc_call('eth_sendTransaction', [transaction])
            
            self.log_transaction(tx_hash, from_address, to_address, amount)
            return tx_hash
        
        except Exception as e:
            self.log_error('send_transaction', e, 
                         from_address=from_address, to_address=to_address, amount=amount)
            raise
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get Ethereum transaction details
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details
        """
        try:
            tx_info = await self._rpc_call('eth_getTransactionByHash', [tx_hash])
            
            if not tx_info:
                raise Exception(f"Transaction not found: {tx_hash}")
            
            # Get transaction receipt for confirmation info
            receipt = None
            try:
                receipt = await self._rpc_call('eth_getTransactionReceipt', [tx_hash])
            except:
                pass
            
            # Calculate confirmations
            confirmations = 0
            if receipt and receipt.get('blockNumber'):
                current_block = await self.get_block_height()
                tx_block = int(receipt['blockNumber'], 16)
                confirmations = current_block - tx_block + 1
            
            return {
                'hash': tx_hash,
                'from': tx_info.get('from'),
                'to': tx_info.get('to'),
                'value': self._wei_to_eth(tx_info.get('value', '0x0')),
                'gas': str(int(tx_info.get('gas', '0x0'), 16)),
                'gasPrice': self._wei_to_eth(tx_info.get('gasPrice', '0x0')),
                'nonce': int(tx_info.get('nonce', '0x0'), 16),
                'blockNumber': int(tx_info.get('blockNumber', '0x0'), 16) if tx_info.get('blockNumber') else None,
                'blockHash': tx_info.get('blockHash'),
                'transactionIndex': int(tx_info.get('transactionIndex', '0x0'), 16) if tx_info.get('transactionIndex') else None,
                'confirmations': confirmations,
                'status': receipt.get('status') if receipt else None
            }
        
        except Exception as e:
            self.log_error('get_transaction', e, tx_hash=tx_hash)
            raise
    
    async def get_block_height(self) -> int:
        """
        Get current Ethereum block height
        
        Returns:
            Current block height
        """
        try:
            block_number = await self._rpc_call('eth_blockNumber')
            return int(block_number, 16)
        except Exception as e:
            self.log_error('get_block_height', e)
            return 0
    
    async def is_node_synced(self) -> bool:
        """
        Check if Ethereum node is synchronized
        
        Returns:
            True if synced, False otherwise
        """
        try:
            sync_status = await self._rpc_call('eth_syncing')
            # eth_syncing returns false when fully synced, or an object when syncing
            return sync_status is False
        except Exception as e:
            self.log_error('is_node_synced', e)
            return False
    
    async def generate_address(self, private_key: Optional[str] = None) -> Dict[str, str]:
        """
        Generate new Ethereum address and private key
        
        Args:
            private_key: Optional existing private key in hex format
            
        Returns:
            Dictionary with 'address' and 'private_key'
        """
        try:
            if private_key:
                # In a real implementation, derive address from private key
                # This is a placeholder
                raise NotImplementedError("Address derivation from private key not implemented")
            else:
                # Generate new account
                address = await self._rpc_call('personal_newAccount', [''])
                
                # Note: In production, you would generate the private key locally
                # and derive the address, rather than relying on the node
                return {
                    'address': address,
                    'private_key': 'placeholder_private_key'  # This should be generated locally
                }
        
        except Exception as e:
            self.log_error('generate_address', e)
            raise
    
    async def get_erc20_balance(self, token_address: str, wallet_address: str) -> str:
        """
        Get ERC-20 token balance
        
        Args:
            token_address: ERC-20 token contract address
            wallet_address: Wallet address to check
            
        Returns:
            Token balance as string
        """
        try:
            # ERC-20 balanceOf function signature
            function_signature = '0x70a08231'  # balanceOf(address)
            
            # Pad wallet address to 32 bytes
            padded_address = wallet_address[2:].zfill(64)
            data = function_signature + padded_address
            
            # Call the contract
            result = await self._rpc_call('eth_call', [{
                'to': token_address,
                'data': data
            }, 'latest'])
            
            # Convert result to decimal
            balance = int(result, 16)
            return str(balance)
        
        except Exception as e:
            self.log_error('get_erc20_balance', e, 
                         token_address=token_address, wallet_address=wallet_address)
            return '0'
    
    async def get_erc20_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Get ERC-20 token information (name, symbol, decimals)
        
        Args:
            token_address: ERC-20 token contract address
            
        Returns:
            Token information dictionary
        """
        try:
            # Function signatures
            name_sig = '0x06fdde03'      # name()
            symbol_sig = '0x95d89b41'    # symbol()
            decimals_sig = '0x313ce567'  # decimals()
            
            # Get token name
            name_result = await self._rpc_call('eth_call', [{
                'to': token_address,
                'data': name_sig
            }, 'latest'])
            
            # Get token symbol
            symbol_result = await self._rpc_call('eth_call', [{
                'to': token_address,
                'data': symbol_sig
            }, 'latest'])
            
            # Get token decimals
            decimals_result = await self._rpc_call('eth_call', [{
                'to': token_address,
                'data': decimals_sig
            }, 'latest'])
            
            # Parse results (simplified - real implementation would decode ABI properly)
            decimals = int(decimals_result, 16)
            
            return {
                'address': token_address,
                'name': 'Token Name',  # Would need proper ABI decoding
                'symbol': 'TOKEN',     # Would need proper ABI decoding
                'decimals': decimals
            }
        
        except Exception as e:
            self.log_error('get_erc20_token_info', e, token_address=token_address)
            return {}
    
    async def send_erc20_transaction(self, token_address: str, from_address: str, 
                                   to_address: str, amount: str, private_key: str) -> str:
        """
        Send ERC-20 token transaction
        
        Args:
            token_address: ERC-20 token contract address
            from_address: Source address
            to_address: Destination address
            amount: Amount to send (in token units)
            private_key: Private key for signing
            
        Returns:
            Transaction hash
        """
        try:
            # ERC-20 transfer function signature
            function_signature = '0xa9059cbb'  # transfer(address,uint256)
            
            # Pad to_address to 32 bytes
            padded_to = to_address[2:].zfill(64)
            
            # Convert amount to hex and pad to 32 bytes
            amount_hex = hex(int(amount))[2:].zfill(64)
            
            # Build transaction data
            data = function_signature + padded_to + amount_hex
            
            # Get nonce
            nonce = await self._rpc_call('eth_getTransactionCount', [from_address, 'pending'])
            
            # Get gas price
            gas_price = await self._rpc_call('eth_gasPrice')
            
            # Build transaction
            transaction = {
                'from': from_address,
                'to': token_address,
                'value': '0x0',  # No ETH value for token transfer
                'gas': hex(100000),  # Higher gas limit for contract interaction
                'gasPrice': gas_price,
                'nonce': nonce,
                'data': data,
                'chainId': hex(self.chain_id)
            }
            
            # Note: In production, sign locally with private key
            tx_hash = await self._rpc_call('eth_sendTransaction', [transaction])
            
            self.log_transaction(tx_hash, from_address, to_address, amount)
            return tx_hash
        
        except Exception as e:
            self.log_error('send_erc20_transaction', e, 
                         token_address=token_address, from_address=from_address, 
                         to_address=to_address, amount=amount)
            raise
    
    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction receipt
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt
        """
        try:
            return await self._rpc_call('eth_getTransactionReceipt', [tx_hash])
        except Exception as e:
            self.log_error('get_transaction_receipt', e, tx_hash=tx_hash)
            return {}
    
    async def get_logs(self, from_block: str = 'latest', to_block: str = 'latest', 
                      address: Optional[str] = None, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get event logs
        
        Args:
            from_block: Starting block
            to_block: Ending block
            address: Contract address filter
            topics: Event topics filter
            
        Returns:
            List of log entries
        """
        try:
            filter_params = {
                'fromBlock': from_block,
                'toBlock': to_block
            }
            
            if address:
                filter_params['address'] = address
            
            if topics:
                filter_params['topics'] = topics
            
            return await self._rpc_call('eth_getLogs', [filter_params])
        
        except Exception as e:
            self.log_error('get_logs', e, from_block=from_block, to_block=to_block)
            return []
    
    async def get_network_id(self) -> int:
        """
        Get network ID
        
        Returns:
            Network ID
        """
        try:
            network_id = await self._rpc_call('net_version')
            return int(network_id)
        except Exception as e:
            self.log_error('get_network_id', e)
            return self.chain_id
    
    async def get_peer_count(self) -> int:
        """
        Get peer count
        
        Returns:
            Number of connected peers
        """
        try:
            peer_count = await self._rpc_call('net_peerCount')
            return int(peer_count, 16)
        except Exception as e:
            self.log_error('get_peer_count', e)
            return 0