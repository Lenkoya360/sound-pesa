"""
Vault integration service for wallet private key management.
"""
import logging
from typing import Optional, Dict, Any
from sound_pesa.vault_client import get_vault_client
from sound_pesa.metrics import track_security_event

logger = logging.getLogger('sound_pesa.security')


class WalletVaultService:
    """
    Service for managing wallet private keys using HashiCorp Vault.
    """
    
    def __init__(self):
        """Initialize Vault service."""
        self.vault_client = get_vault_client()
    
    def store_wallet_private_key(self, wallet_id: str, blockchain: str, 
                                private_key: str, user_id: str) -> bool:
        """
        Securely store wallet private key in Vault.
        
        Args:
            wallet_id: Unique wallet identifier
            blockchain: Blockchain name (bitcoin, ethereum, etc.)
            private_key: Private key to encrypt and store
            user_id: User ID for audit logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store encrypted private key
            success = self.vault_client.store_private_key(
                wallet_id=wallet_id,
                blockchain=blockchain,
                private_key=private_key
            )
            
            if success:
                # Log security event
                logger.info({
                    'event_type': 'private_key_stored',
                    'wallet_id': wallet_id,
                    'blockchain': blockchain,
                    'user_id': user_id,
                    'success': True
                })
            else:
                # Log failure
                logger.error({
                    'event_type': 'private_key_store_failed',
                    'wallet_id': wallet_id,
                    'blockchain': blockchain,
                    'user_id': user_id,
                    'success': False
                })
                
                # Track security metric
                track_security_event(
                    'suspicious_transaction',
                    blockchain=blockchain,
                    reason='private_key_storage_failure'
                )
            
            return success
            
        except Exception as e:
            logger.error({
                'event_type': 'private_key_store_error',
                'wallet_id': wallet_id,
                'blockchain': blockchain,
                'user_id': user_id,
                'error': str(e)
            })
            return False
    
    def retrieve_wallet_private_key(self, wallet_id: str, blockchain: str, 
                                   user_id: str) -> Optional[str]:
        """
        Retrieve and decrypt wallet private key from Vault.
        
        Args:
            wallet_id: Unique wallet identifier
            blockchain: Blockchain name
            user_id: User ID for audit logging
            
        Returns:
            Decrypted private key or None if not found/failed
        """
        try:
            # Retrieve private key
            private_key = self.vault_client.get_private_key(
                wallet_id=wallet_id,
                blockchain=blockchain
            )
            
            if private_key:
                # Log successful retrieval (without the key itself)
                logger.info({
                    'event_type': 'private_key_retrieved',
                    'wallet_id': wallet_id,
                    'blockchain': blockchain,
                    'user_id': user_id,
                    'success': True
                })
            else:
                # Log failure
                logger.warning({
                    'event_type': 'private_key_retrieval_failed',
                    'wallet_id': wallet_id,
                    'blockchain': blockchain,
                    'user_id': user_id,
                    'success': False
                })
            
            return private_key
            
        except Exception as e:
            logger.error({
                'event_type': 'private_key_retrieval_error',
                'wallet_id': wallet_id,
                'blockchain': blockchain,
                'user_id': user_id,
                'error': str(e)
            })
            return None
    
    def rotate_wallet_encryption_key(self, user_id: str) -> bool:
        """
        Rotate the encryption key used for private keys.
        
        Args:
            user_id: User ID initiating the rotation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.vault_client.rotate_encryption_key('private-keys')
            
            if success:
                logger.info({
                    'event_type': 'encryption_key_rotated',
                    'key_name': 'private-keys',
                    'user_id': user_id,
                    'success': True
                })
            else:
                logger.error({
                    'event_type': 'encryption_key_rotation_failed',
                    'key_name': 'private-keys',
                    'user_id': user_id,
                    'success': False
                })
            
            return success
            
        except Exception as e:
            logger.error({
                'event_type': 'encryption_key_rotation_error',
                'key_name': 'private-keys',
                'user_id': user_id,
                'error': str(e)
            })
            return False
    
    def store_api_credentials(self, service_name: str, credentials: Dict[str, str], 
                             user_id: str) -> bool:
        """
        Store API credentials for external services.
        
        Args:
            service_name: Name of the external service
            credentials: Dictionary of credential key-value pairs
            user_id: User ID for audit logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt sensitive credentials
            encrypted_credentials = {}
            for key, value in credentials.items():
                if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
                    encrypted_value = self.vault_client.encrypt_data('api-keys', value)
                    if encrypted_value:
                        encrypted_credentials[f"encrypted_{key}"] = encrypted_value
                    else:
                        logger.error(f"Failed to encrypt credential: {key}")
                        return False
                else:
                    encrypted_credentials[key] = value
            
            # Store in Vault
            path = f"api-credentials/{service_name}"
            success = self.vault_client.store_secret(path, encrypted_credentials)
            
            if success:
                logger.info({
                    'event_type': 'api_credentials_stored',
                    'service_name': service_name,
                    'user_id': user_id,
                    'credential_count': len(credentials)
                })
            else:
                logger.error({
                    'event_type': 'api_credentials_store_failed',
                    'service_name': service_name,
                    'user_id': user_id
                })
            
            return success
            
        except Exception as e:
            logger.error({
                'event_type': 'api_credentials_store_error',
                'service_name': service_name,
                'user_id': user_id,
                'error': str(e)
            })
            return False
    
    def get_api_credentials(self, service_name: str, user_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt API credentials for external services.
        
        Args:
            service_name: Name of the external service
            user_id: User ID for audit logging
            
        Returns:
            Dictionary of decrypted credentials or None if failed
        """
        try:
            # Retrieve encrypted credentials
            path = f"api-credentials/{service_name}"
            encrypted_credentials = self.vault_client.get_secret(path, use_cache=False)
            
            if not encrypted_credentials:
                logger.warning({
                    'event_type': 'api_credentials_not_found',
                    'service_name': service_name,
                    'user_id': user_id
                })
                return None
            
            # Decrypt sensitive credentials
            decrypted_credentials = {}
            for key, value in encrypted_credentials.items():
                if key.startswith('encrypted_'):
                    original_key = key.replace('encrypted_', '')
                    decrypted_value = self.vault_client.decrypt_data('api-keys', value)
                    if decrypted_value:
                        decrypted_credentials[original_key] = decrypted_value
                    else:
                        logger.error(f"Failed to decrypt credential: {original_key}")
                        return None
                else:
                    decrypted_credentials[key] = value
            
            logger.info({
                'event_type': 'api_credentials_retrieved',
                'service_name': service_name,
                'user_id': user_id,
                'credential_count': len(decrypted_credentials)
            })
            
            return decrypted_credentials
            
        except Exception as e:
            logger.error({
                'event_type': 'api_credentials_retrieval_error',
                'service_name': service_name,
                'user_id': user_id,
                'error': str(e)
            })
            return None
    
    def audit_vault_access(self, operation: str, resource: str, user_id: str, 
                          success: bool, details: Optional[Dict[str, Any]] = None):
        """
        Log Vault access for security auditing.
        
        Args:
            operation: Type of operation (read, write, delete, etc.)
            resource: Resource being accessed
            user_id: User performing the operation
            success: Whether the operation was successful
            details: Additional details about the operation
        """
        audit_log = {
            'event_type': 'vault_access_audit',
            'operation': operation,
            'resource': resource,
            'user_id': user_id,
            'success': success,
            'timestamp': logger.info.__self__.name  # Current timestamp will be added by formatter
        }
        
        if details:
            audit_log['details'] = details
        
        if success:
            logger.info(audit_log)
        else:
            logger.warning(audit_log)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Vault integration.
        
        Returns:
            Health status dictionary
        """
        return self.vault_client.health_check()