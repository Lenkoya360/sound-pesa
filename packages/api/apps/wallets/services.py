"""
Wallet management services and utilities.
"""
import logging
import secrets
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from cryptography.fernet import Fernet
from .models import Wallet, WalletBalance, WalletTransaction

logger = logging.getLogger(__name__)


class WalletService:
    """
    Service class for wallet operations.
    """
    
    @staticmethod
    def generate_private_key() -> str:
        """
        Generate a cryptographically secure private key.
        """
        return secrets.token_hex(32)
    
    @staticmethod
    def encrypt_private_key(private_key: str) -> str:
        """
        Encrypt private key for secure storage.
        Note: In production, this should use HashiCorp Vault or similar.
        """
        # For now, using a simple encryption. In production, integrate with Vault
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        f = Fernet(Fernet.generate_key())  # This should be from Vault
        encrypted_key = f.encrypt(private_key.encode())
        return encrypted_key.decode()
    
    @staticmethod
    def decrypt_private_key(encrypted_private_key: str) -> str:
        """
        Decrypt private key for transaction signing.
        Note: In production, this should use HashiCorp Vault or similar.
        """
        # Placeholder implementation - integrate with Vault in production
        return "decrypted_private_key_placeholder"
    
    @staticmethod
    def generate_address(blockchain: str, private_key: str) -> str:
        """
        Generate blockchain address from private key.
        This is a placeholder - actual implementation will be in blockchain adapters.
        """
        address_prefixes = {
            'bitcoin': '1',
            'ethereum': '0x',
            'cardano': 'addr1',
            'polkadot': '1'
        }
        
        prefix = address_prefixes.get(blockchain, '1')
        # Generate a mock address for now
        address_suffix = secrets.token_hex(20)
        return f"{prefix}{address_suffix}"
    
    @classmethod
    def create_wallet(cls, user, blockchain: str) -> Wallet:
        """
        Create a new wallet for the user on the specified blockchain.
        """
        try:
            with transaction.atomic():
                # Generate private key and address
                private_key = cls.generate_private_key()
                encrypted_private_key = cls.encrypt_private_key(private_key)
                address = cls.generate_address(blockchain, private_key)
                
                # Create wallet
                wallet = Wallet.objects.create(
                    user=user,
                    blockchain=blockchain,
                    address=address,
                    encrypted_private_key=encrypted_private_key
                )
                
                # Create initial balance record
                WalletBalance.objects.create(wallet=wallet)
                
                logger.info(f"Created {blockchain} wallet for user {user.email}: {address}")
                return wallet
                
        except Exception as e:
            logger.error(f"Failed to create {blockchain} wallet for user {user.email}: {str(e)}")
            raise
    
    @classmethod
    def create_all_wallets(cls, user) -> Dict[str, Wallet]:
        """
        Create wallets for all supported blockchains.
        """
        wallets = {}
        
        for blockchain_code, blockchain_name in Wallet.BLOCKCHAIN_CHOICES:
            try:
                # Check if wallet already exists
                existing_wallet = Wallet.objects.filter(
                    user=user, 
                    blockchain=blockchain_code
                ).first()
                
                if existing_wallet:
                    wallets[blockchain_code] = existing_wallet
                else:
                    wallets[blockchain_code] = cls.create_wallet(user, blockchain_code)
                    
            except Exception as e:
                logger.error(f"Failed to create {blockchain_code} wallet: {str(e)}")
                continue
        
        return wallets
    
    @staticmethod
    def get_wallet_balance(wallet: Wallet) -> Optional[WalletBalance]:
        """
        Get current balance for a wallet.
        """
        try:
            balance, created = WalletBalance.objects.get_or_create(wallet=wallet)
            return balance
        except Exception as e:
            logger.error(f"Failed to get balance for wallet {wallet.id}: {str(e)}")
            return None
    
    @staticmethod
    def update_wallet_balance(wallet: Wallet, balance: Decimal, 
                            confirmed_balance: Decimal = None, 
                            unconfirmed_balance: Decimal = None) -> bool:
        """
        Update wallet balance information.
        """
        try:
            wallet_balance, created = WalletBalance.objects.get_or_create(wallet=wallet)
            
            wallet_balance.balance = balance
            if confirmed_balance is not None:
                wallet_balance.confirmed_balance = confirmed_balance
            if unconfirmed_balance is not None:
                wallet_balance.unconfirmed_balance = unconfirmed_balance
            
            wallet_balance.save()
            
            logger.info(f"Updated balance for wallet {wallet.id}: {balance}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update balance for wallet {wallet.id}: {str(e)}")
            return False
    
    @staticmethod
    def get_transaction_history(wallet: Wallet, limit: int = 50) -> list:
        """
        Get transaction history for a wallet.
        """
        try:
            transactions = WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')[:limit]
            
            return list(transactions)
            
        except Exception as e:
            logger.error(f"Failed to get transaction history for wallet {wallet.id}: {str(e)}")
            return []
    
    @staticmethod
    def record_transaction(wallet: Wallet, transaction_data: Dict[str, Any]) -> Optional[WalletTransaction]:
        """
        Record a new transaction for a wallet.
        """
        try:
            transaction_obj = WalletTransaction.objects.create(
                wallet=wallet,
                **transaction_data
            )
            
            logger.info(f"Recorded transaction {transaction_obj.id} for wallet {wallet.id}")
            return transaction_obj
            
        except Exception as e:
            logger.error(f"Failed to record transaction for wallet {wallet.id}: {str(e)}")
            return None