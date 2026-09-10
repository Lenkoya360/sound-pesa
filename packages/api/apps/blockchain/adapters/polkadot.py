"""
Polkadot blockchain adapter implementation
"""

import asyncio
import json
import websockets
from typing import Dict, Any, Optional, List
from decimal import Decimal
import re

from .base import BaseBlockchainAdapter


class PolkadotAdapter(BaseBlockchainAdapter):
    """
    Polkadot blockchain adapter for Substrate node integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.existential_deposit = Decimal(config.get('existential_deposit', '10000000000'))  # 1 DOT
        
        # Polkadot constants
        self.PLANCK_PER_DOT = Decimal('10000000000')  # 1 DOT = 10^10 planck
        
        # Convert HTTP URL to WebSocket URL if needed
        if self.rpc_url.startswith('http'):
            self.rpc_url = self.rpc_url.replace('http', 'ws')
    
    async def _rpc_call(self, method: str, params: List[Any] = None) -> Any:
        """
        Make WebSocket RPC call to Polkadot node
        
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
        
        try:
            async with websockets.connect(
                self.rpc_url,
                timeout=30,
                ping_interval=None
            ) as websocket:
                await websocket.send(json.dumps(payload))
                response = await websocket.recv()
                result = json.loads(response)
                
                if 'error' in result and result['error']:
                    raise Exception(f"RPC error: {result['error']}")
                
                return result.get('result')
        
        except Exception as e:
            self.log_error('rpc_call', e, method=method, params=params)
            raise
    
    def validate_address(self, address: str) -> bool:
        """
        Validate Polkadot address format (SS58)
        
        Args:
            address: Polkadot address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not address or not isinstance(address, str):
            return False
        
        # Polkadot addresses use SS58 format
        # They typically start with 1 and are 47-48 characters long
        return self.validate_address_format(address, r'^[1-9A-HJ-NP-Za-km-z]{47,48}$')
    
    def _planck_to_dot(self, planck: str) -> str:
        """Convert planck to DOT"""
        planck_decimal = Decimal(planck)
        dot_decimal = planck_decimal / self.PLANCK_PER_DOT
        return str(dot_decimal)
    
    def _dot_to_planck(self, dot: str) -> str:
        """Convert DOT to planck"""
        dot_decimal = Decimal(dot)
        planck_decimal = dot_decimal * self.PLANCK_PER_DOT
        return str(int(planck_decimal))
    
    async def get_balance(self, address: str) -> str:
        """
        Get Polkadot balance for address
        
        Args:
            address: Polkadot address
            
        Returns:
            Balance in DOT as string
        """
        try:
            # Get account info
            account_info = await self._rpc_call('system_account', [address])
            
            if not account_info or 'data' not in account_info:
                return '0'
            
            # Extract free balance
            free_balance = account_info['data'].get('free', '0')
            return self._planck_to_dot(str(free_balance))
        
        except Exception as e:
            self.log_error('get_balance', e, address=address)
            return '0'
    
    async def estimate_fee(self, from_address: str, to_address: str, amount: str) -> str:
        """
        Estimate Polkadot transaction fee
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in DOT
            
        Returns:
            Estimated fee in DOT
        """
        try:
            # Create a transfer call
            call = {
                'module': 'Balances',
                'call': 'transfer',
                'args': {
                    'dest': to_address,
                    'value': self._dot_to_planck(amount)
                }
            }
            
            # Get payment info (fee estimation)
            payment_info = await self._rpc_call('payment_queryInfo', [call, None])
            
            if payment_info and 'partialFee' in payment_info:
                fee_planck = payment_info['partialFee']
                return self._planck_to_dot(str(fee_planck))
            
            # Default fee estimate
            return '0.01'
        
        except Exception as e:
            self.log_error('estimate_fee', e, from_address=from_address, to_address=to_address)
            return '0.01'  # Default fee estimate in DOT
    
    async def send_transaction(self, from_address: str, to_address: str, 
                             amount: str, private_key: str) -> str:
        """
        Send Polkadot transaction
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send in DOT
            private_key: Private key for signing
            
        Returns:
            Transaction hash
        """
        try:
            # Note: This is a placeholder implementation
            # Real Polkadot transaction creation requires:
            # 1. Creating and signing extrinsic with proper libraries
            # 2. Submitting to network
            # 3. Monitoring for inclusion in block
            
            # For now, this is a mock implementation
            raise NotImplementedError("Polkadot transaction sending not fully implemented")
        
        except Exception as e:
            self.log_error('send_transaction', e, 
                         from_address=from_address, to_address=to_address, amount=amount)
            raise
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get Polkadot transaction details
        
        Args:
            tx_hash: Transaction hash (extrinsic hash)
            
        Returns:
            Transaction details
        """
        try:
            # Get block hash containing the extrinsic
            block_hash = await self._rpc_call('chain_getBlockHash', [])
            
            # Get block details
            block = await self._rpc_call('chain_getBlock', [block_hash])
            
            # Find extrinsic in block
            extrinsic = None
            extrinsic_index = None
            
            for i, ext in enumerate(block['block']['extrinsics']):
                # This is simplified - would need proper hash calculation
                if ext.get('hash') == tx_hash:
                    extrinsic = ext
                    extrinsic_index = i
                    break
            
            if not extrinsic:
                raise Exception(f"Extrinsic not found: {tx_hash}")
            
            return {
                'hash': tx_hash,
                'block_hash': block_hash,
                'block_number': block['block']['header']['number'],
                'extrinsic_index': extrinsic_index,
                'method': extrinsic.get('method', {}),
                'signature': extrinsic.get('signature'),
                'nonce': extrinsic.get('nonce'),
                'tip': extrinsic.get('tip', '0'),
                'success': True  # Would need to check events for actual status
            }
        
        except Exception as e:
            self.log_error('get_transaction', e, tx_hash=tx_hash)
            raise
    
    async def get_block_height(self) -> int:
        """
        Get current Polkadot block height
        
        Returns:
            Current block height
        """
        try:
            header = await self._rpc_call('chain_getHeader')
            return int(header.get('number', '0x0'), 16)
        except Exception as e:
            self.log_error('get_block_height', e)
            return 0
    
    async def is_node_synced(self) -> bool:
        """
        Check if Polkadot node is synchronized
        
        Returns:
            True if synced, False otherwise
        """
        try:
            health = await self._rpc_call('system_health')
            return health.get('isSyncing', True) == False
        except Exception as e:
            self.log_error('is_node_synced', e)
            return False
    
    async def generate_address(self, private_key: Optional[str] = None) -> Dict[str, str]:
        """
        Generate new Polkadot address and private key
        
        Args:
            private_key: Optional existing private key
            
        Returns:
            Dictionary with 'address' and 'private_key'
        """
        try:
            # Note: This is a placeholder implementation
            # Real Polkadot address generation requires:
            # 1. Generating or using existing private key
            # 2. Deriving public key using Sr25519 or Ed25519
            # 3. Encoding address using SS58 format
            
            raise NotImplementedError("Polkadot address generation not fully implemented")
        
        except Exception as e:
            self.log_error('generate_address', e)
            raise
    
    async def get_account_info(self, address: str) -> Dict[str, Any]:
        """
        Get detailed account information
        
        Args:
            address: Polkadot address
            
        Returns:
            Account information dictionary
        """
        try:
            return await self._rpc_call('system_account', [address])
        except Exception as e:
            self.log_error('get_account_info', e, address=address)
            return {}
    
    async def get_staking_info(self, address: str) -> Dict[str, Any]:
        """
        Get staking information for address
        
        Args:
            address: Polkadot address
            
        Returns:
            Staking information dictionary
        """
        try:
            # Get staking ledger
            staking_ledger = await self._rpc_call('staking_ledger', [address])
            
            # Get bonded amount
            bonded = await self._rpc_call('staking_bonded', [address])
            
            return {
                'bonded': self._planck_to_dot(str(bonded or '0')),
                'ledger': staking_ledger,
                'active': staking_ledger.get('active', '0') if staking_ledger else '0',
                'unlocking': staking_ledger.get('unlocking', []) if staking_ledger else []
            }
        
        except Exception as e:
            self.log_error('get_staking_info', e, address=address)
            return {}
    
    async def get_runtime_version(self) -> Dict[str, Any]:
        """
        Get runtime version information
        
        Returns:
            Runtime version dictionary
        """
        try:
            return await self._rpc_call('state_getRuntimeVersion')
        except Exception as e:
            self.log_error('get_runtime_version', e)
            return {}
    
    async def submit_extrinsic(self, signed_extrinsic: str) -> str:
        """
        Submit a signed extrinsic to the network
        
        Args:
            signed_extrinsic: Signed extrinsic in hex format
            
        Returns:
            Extrinsic hash
        """
        try:
            return await self._rpc_call('author_submitExtrinsic', [signed_extrinsic])
        except Exception as e:
            self.log_error('submit_extrinsic', e, signed_extrinsic=signed_extrinsic[:20])
            raise
    
    async def bond_funds(self, controller: str, value: str, payee: str) -> Dict[str, Any]:
        """
        Bond funds for staking
        
        Args:
            controller: Controller account address
            value: Amount to bond in planck
            payee: Reward destination
            
        Returns:
            Bonding operation result
        """
        try:
            # Note: This would require proper extrinsic creation and signing
            # For now, this is a placeholder
            raise NotImplementedError("Polkadot staking operations not fully implemented")
        
        except Exception as e:
            self.log_error('bond_funds', e, controller=controller, value=value)
            raise
    
    async def nominate_validators(self, targets: List[str]) -> Dict[str, Any]:
        """
        Nominate validators for staking
        
        Args:
            targets: List of validator addresses to nominate
            
        Returns:
            Nomination operation result
        """
        try:
            # Note: This would require proper extrinsic creation and signing
            # For now, this is a placeholder
            raise NotImplementedError("Polkadot nomination not fully implemented")
        
        except Exception as e:
            self.log_error('nominate_validators', e, targets=targets)
            raise
    
    async def unbond_funds(self, value: str) -> Dict[str, Any]:
        """
        Unbond staked funds
        
        Args:
            value: Amount to unbond in planck
            
        Returns:
            Unbonding operation result
        """
        try:
            # Note: This would require proper extrinsic creation and signing
            # For now, this is a placeholder
            raise NotImplementedError("Polkadot unbonding not fully implemented")
        
        except Exception as e:
            self.log_error('unbond_funds', e, value=value)
            raise
    
    async def get_validator_info(self, validator_address: str) -> Dict[str, Any]:
        """
        Get validator information
        
        Args:
            validator_address: Validator address
            
        Returns:
            Validator information dictionary
        """
        try:
            # Get validator preferences
            prefs = await self._rpc_call('query_staking_validators', [validator_address])
            
            # Get validator exposure
            exposure = await self._rpc_call('query_staking_erasStakers', [None, validator_address])
            
            return {
                'address': validator_address,
                'preferences': prefs,
                'exposure': exposure,
                'commission': prefs.get('commission', 0) if prefs else 0
            }
        
        except Exception as e:
            self.log_error('get_validator_info', e, validator_address=validator_address)
            return {}
    
    async def get_era_info(self) -> Dict[str, Any]:
        """
        Get current era information
        
        Returns:
            Era information dictionary
        """
        try:
            current_era = await self._rpc_call('query_staking_currentEra')
            active_era = await self._rpc_call('query_staking_activeEra')
            
            return {
                'current_era': current_era,
                'active_era': active_era
            }
        
        except Exception as e:
            self.log_error('get_era_info', e)
            return {}
    
    async def monitor_extrinsic_status(self, ext_hash: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Monitor extrinsic status until finalized or timeout
        
        Args:
            ext_hash: Extrinsic hash to monitor
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            Final extrinsic status
        """
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # Check if extrinsic is in a block
                ext_info = await self.get_transaction(ext_hash)
                
                if ext_info.get('block_hash'):
                    # Get block finalization status
                    finalized_head = await self._rpc_call('chain_getFinalizedHead')
                    
                    if ext_info.get('block_hash') == finalized_head:
                        return {
                            'status': 'finalized',
                            'block_hash': ext_info.get('block_hash'),
                            'block_number': ext_info.get('block_number')
                        }
                    else:
                        return {
                            'status': 'in_block',
                            'block_hash': ext_info.get('block_hash'),
                            'block_number': ext_info.get('block_number')
                        }
                
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > max_wait_time:
                    return {
                        'status': 'timeout'
                    }
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                self.log_error('monitor_extrinsic_status', e, ext_hash=ext_hash)
                return {
                    'status': 'error',
                    'error': str(e)
                }