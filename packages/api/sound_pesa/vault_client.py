"""
HashiCorp Vault client for Sound Pesa platform.
Handles secure storage and retrieval of secrets, private keys, and sensitive configuration.
"""
import os
import json
import logging
import hvac
from typing import Dict, Any, Optional
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class VaultClient:
    """
    HashiCorp Vault client for secure secrets management.
    """
    
    def __init__(self):
        """Initialize Vault client with configuration."""
        self.vault_url = os.getenv('VAULT_ADDR', 'http://vault:8200')
        self.vault_token = os.getenv('VAULT_TOKEN')
        self.vault_namespace = os.getenv('VAULT_NAMESPACE', 'sound-pesa')
        
        # Initialize HVAC client
        self.client = hvac.Client(
            url=self.vault_url,
            token=self.vault_token
        )
        
        # Verify client is authenticated
        if not self.client.is_authenticated():
            logger.error("Vault client is not authenticated")
            raise Exception("Failed to authenticate with Vault")
        
        # Initialize secret engines
        self._setup_secret_engines()
    
    def _setup_secret_engines(self):
        """Set up required secret engines in Vault."""
        try:
            # Enable KV v2 secrets engine for application secrets
            if 'kv/' not in self.client.sys.list_mounted_secrets_engines():
                self.client.sys.enable_secrets_engine(
                    backend_type='kv',
                    path='kv',
                    options={'version': '2'}
                )
                logger.info("Enabled KV v2 secrets engine")
            
            # Enable database secrets engine for dynamic credentials
            if 'database/' not in self.client.sys.list_mounted_secrets_engines():
                self.client.sys.enable_secrets_engine(
                    backend_type='database',
                    path='database'
                )
                logger.info("Enabled database secrets engine")
            
            # Enable transit secrets engine for encryption
            if 'transit/' not in self.client.sys.list_mounted_secrets_engines():
                self.client.sys.enable_secrets_engine(
                    backend_type='transit',
                    path='transit'
                )
                logger.info("Enabled transit secrets engine")
                
                # Create encryption key for private keys
                self._create_encryption_key('private-keys')
                self._create_encryption_key('api-keys')
            
        except Exception as e:
            logger.error(f"Failed to setup secret engines: {str(e)}")
    
    def _create_encryption_key(self, key_name: str):
        """Create encryption key in transit engine."""
        try:
            self.client.secrets.transit.create_key(
                name=key_name,
                key_type='aes256-gcm96'
            )
            logger.info(f"Created encryption key: {key_name}")
        except Exception as e:
            if "path already exists" not in str(e):
                logger.error(f"Failed to create encryption key {key_name}: {str(e)}")
    
    def store_secret(self, path: str, secret_data: Dict[str, Any]) -> bool:
        """
        Store secret in Vault KV store.
        
        Args:
            path: Secret path (e.g., 'app/database')
            secret_data: Dictionary of secret key-value pairs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = f"{self.vault_namespace}/{path}"
            self.client.secrets.kv.v2.create_or_update_secret(
                path=full_path,
                secret=secret_data
            )
            logger.info(f"Stored secret at path: {full_path}")
            
            # Clear cache for this path
            cache_key = f"vault_secret_{full_path}"
            cache.delete(cache_key)
            
            return True
        except Exception as e:
            logger.error(f"Failed to store secret at {path}: {str(e)}")
            return False
    
    def get_secret(self, path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve secret from Vault KV store.
        
        Args:
            path: Secret path
            use_cache: Whether to use cached values
            
        Returns:
            Secret data dictionary or None if not found
        """
        try:
            full_path = f"{self.vault_namespace}/{path}"
            cache_key = f"vault_secret_{full_path}"
            
            # Check cache first
            if use_cache:
                cached_secret = cache.get(cache_key)
                if cached_secret:
                    return cached_secret
            
            # Retrieve from Vault
            response = self.client.secrets.kv.v2.read_secret_version(path=full_path)
            secret_data = response['data']['data']
            
            # Cache for 5 minutes
            if use_cache:
                cache.set(cache_key, secret_data, 300)
            
            logger.debug(f"Retrieved secret from path: {full_path}")
            return secret_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret from {path}: {str(e)}")
            return None
    
    def encrypt_data(self, key_name: str, plaintext: str) -> Optional[str]:
        """
        Encrypt data using Vault transit engine.
        
        Args:
            key_name: Name of the encryption key
            plaintext: Data to encrypt
            
        Returns:
            Encrypted data (base64 encoded) or None if failed
        """
        try:
            # Encode plaintext to base64
            plaintext_b64 = base64.b64encode(plaintext.encode()).decode()
            
            # Encrypt using Vault
            response = self.client.secrets.transit.encrypt_data(
                name=key_name,
                plaintext=plaintext_b64
            )
            
            encrypted_data = response['data']['ciphertext']
            logger.debug(f"Encrypted data using key: {key_name}")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Failed to encrypt data with key {key_name}: {str(e)}")
            return None
    
    def decrypt_data(self, key_name: str, ciphertext: str) -> Optional[str]:
        """
        Decrypt data using Vault transit engine.
        
        Args:
            key_name: Name of the encryption key
            ciphertext: Encrypted data to decrypt
            
        Returns:
            Decrypted plaintext or None if failed
        """
        try:
            # Decrypt using Vault
            response = self.client.secrets.transit.decrypt_data(
                name=key_name,
                ciphertext=ciphertext
            )
            
            # Decode from base64
            plaintext_b64 = response['data']['plaintext']
            plaintext = base64.b64decode(plaintext_b64).decode()
            
            logger.debug(f"Decrypted data using key: {key_name}")
            return plaintext
            
        except Exception as e:
            logger.error(f"Failed to decrypt data with key {key_name}: {str(e)}")
            return None
    
    def store_private_key(self, wallet_id: str, blockchain: str, private_key: str) -> bool:
        """
        Store encrypted private key in Vault.
        
        Args:
            wallet_id: Unique wallet identifier
            blockchain: Blockchain name
            private_key: Private key to encrypt and store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt private key
            encrypted_key = self.encrypt_data('private-keys', private_key)
            if not encrypted_key:
                return False
            
            # Store in KV store
            path = f"wallets/{blockchain}/{wallet_id}"
            secret_data = {
                'encrypted_private_key': encrypted_key,
                'blockchain': blockchain,
                'wallet_id': wallet_id,
                'created_at': str(datetime.utcnow())
            }
            
            return self.store_secret(path, secret_data)
            
        except Exception as e:
            logger.error(f"Failed to store private key for wallet {wallet_id}: {str(e)}")
            return False
    
    def get_private_key(self, wallet_id: str, blockchain: str) -> Optional[str]:
        """
        Retrieve and decrypt private key from Vault.
        
        Args:
            wallet_id: Unique wallet identifier
            blockchain: Blockchain name
            
        Returns:
            Decrypted private key or None if not found
        """
        try:
            # Retrieve encrypted key
            path = f"wallets/{blockchain}/{wallet_id}"
            secret_data = self.get_secret(path, use_cache=False)  # Don't cache private keys
            
            if not secret_data:
                return None
            
            encrypted_key = secret_data.get('encrypted_private_key')
            if not encrypted_key:
                return None
            
            # Decrypt private key
            private_key = self.decrypt_data('private-keys', encrypted_key)
            return private_key
            
        except Exception as e:
            logger.error(f"Failed to retrieve private key for wallet {wallet_id}: {str(e)}")
            return None
    
    def setup_database_credentials(self, db_config: Dict[str, str]) -> bool:
        """
        Configure database dynamic credentials in Vault.
        
        Args:
            db_config: Database connection configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Configure database connection
            self.client.secrets.database.configure(
                name='postgresql-soundpesa',
                plugin_name='postgresql-database-plugin',
                connection_url=f"postgresql://{{{{username}}}}:{{{{password}}}}@{db_config['host']}:{db_config['port']}/{db_config['database']}?sslmode=disable",
                allowed_roles=['soundpesa-app'],
                username=db_config['username'],
                password=db_config['password']
            )
            
            # Create role for application
            self.client.secrets.database.create_role(
                name='soundpesa-app',
                db_name='postgresql-soundpesa',
                creation_statements=[
                    "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
                    "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";"
                ],
                default_ttl='1h',
                max_ttl='24h'
            )
            
            logger.info("Configured database dynamic credentials")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup database credentials: {str(e)}")
            return False
    
    def get_database_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get dynamic database credentials from Vault.
        
        Returns:
            Dictionary with username and password or None if failed
        """
        try:
            response = self.client.secrets.database.generate_credentials(
                name='soundpesa-app'
            )
            
            credentials = {
                'username': response['data']['username'],
                'password': response['data']['password']
            }
            
            logger.info("Generated dynamic database credentials")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get database credentials: {str(e)}")
            return None
    
    def rotate_encryption_key(self, key_name: str) -> bool:
        """
        Rotate encryption key in Vault.
        
        Args:
            key_name: Name of the key to rotate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.secrets.transit.rotate_key(name=key_name)
            logger.info(f"Rotated encryption key: {key_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate key {key_name}: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Vault connection.
        
        Returns:
            Health status dictionary
        """
        try:
            # Check if client is authenticated
            is_authenticated = self.client.is_authenticated()
            
            # Check seal status
            seal_status = self.client.sys.read_seal_status()
            
            # Check if required engines are mounted
            mounted_engines = self.client.sys.list_mounted_secrets_engines()
            required_engines = ['kv/', 'database/', 'transit/']
            engines_ok = all(engine in mounted_engines for engine in required_engines)
            
            return {
                'vault_url': self.vault_url,
                'authenticated': is_authenticated,
                'sealed': seal_status['sealed'],
                'engines_mounted': engines_ok,
                'version': seal_status.get('version', 'unknown'),
                'healthy': is_authenticated and not seal_status['sealed'] and engines_ok
            }
            
        except Exception as e:
            logger.error(f"Vault health check failed: {str(e)}")
            return {
                'vault_url': self.vault_url,
                'authenticated': False,
                'sealed': True,
                'engines_mounted': False,
                'healthy': False,
                'error': str(e)
            }


# Global Vault client instance
_vault_client = None

def get_vault_client() -> VaultClient:
    """Get global Vault client instance."""
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
    return _vault_client