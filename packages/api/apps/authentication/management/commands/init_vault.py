"""
Management command to initialize HashiCorp Vault for Sound Pesa platform.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from sound_pesa.vault_client import get_vault_client


class Command(BaseCommand):
    help = 'Initialize HashiCorp Vault with required secrets and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup-db',
            action='store_true',
            help='Setup database dynamic credentials',
        )
        parser.add_argument(
            '--store-secrets',
            action='store_true',
            help='Store application secrets in Vault',
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Perform Vault health check',
        )

    def handle(self, *args, **options):
        """Initialize Vault configuration."""
        try:
            vault_client = get_vault_client()
            
            if options['health_check']:
                self._health_check(vault_client)
            
            if options['setup_db']:
                self._setup_database_credentials(vault_client)
            
            if options['store_secrets']:
                self._store_application_secrets(vault_client)
            
            if not any([options['health_check'], options['setup_db'], options['store_secrets']]):
                # Run all operations by default
                self._health_check(vault_client)
                self._setup_database_credentials(vault_client)
                self._store_application_secrets(vault_client)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully initialized Vault configuration')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize Vault: {str(e)}')
            )
    
    def _health_check(self, vault_client):
        """Perform Vault health check."""
        self.stdout.write('Performing Vault health check...')
        
        health_status = vault_client.health_check()
        
        if health_status['healthy']:
            self.stdout.write(
                self.style.SUCCESS('✓ Vault is healthy and ready')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Vault health check failed')
            )
            
        self.stdout.write(f"  URL: {health_status['vault_url']}")
        self.stdout.write(f"  Authenticated: {health_status['authenticated']}")
        self.stdout.write(f"  Sealed: {health_status['sealed']}")
        self.stdout.write(f"  Engines Mounted: {health_status['engines_mounted']}")
        
        if 'error' in health_status:
            self.stdout.write(f"  Error: {health_status['error']}")
    
    def _setup_database_credentials(self, vault_client):
        """Setup database dynamic credentials."""
        self.stdout.write('Setting up database dynamic credentials...')
        
        db_config = {
            'host': os.getenv('DB_HOST', 'postgres'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'soundpesa'),
            'username': os.getenv('DB_USER', 'soundpesa'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        success = vault_client.setup_database_credentials(db_config)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✓ Database credentials configured')
            )
            
            # Test credential generation
            creds = vault_client.get_database_credentials()
            if creds:
                self.stdout.write(
                    self.style.SUCCESS('✓ Dynamic credentials generation working')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Dynamic credentials generation failed')
                )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to configure database credentials')
            )
    
    def _store_application_secrets(self, vault_client):
        """Store application secrets in Vault."""
        self.stdout.write('Storing application secrets...')
        
        # Django secret key
        django_secrets = {
            'secret_key': os.getenv('SECRET_KEY', settings.SECRET_KEY),
            'debug': str(settings.DEBUG),
            'allowed_hosts': ','.join(settings.ALLOWED_HOSTS)
        }
        
        success = vault_client.store_secret('app/django', django_secrets)
        if success:
            self.stdout.write(
                self.style.SUCCESS('✓ Django secrets stored')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to store Django secrets')
            )
        
        # JWT secrets
        jwt_secrets = {
            'signing_key': os.getenv('JWT_SIGNING_KEY', settings.SECRET_KEY),
            'algorithm': 'HS256',
            'access_token_lifetime': '3600',  # 1 hour
            'refresh_token_lifetime': '604800'  # 7 days
        }
        
        success = vault_client.store_secret('app/jwt', jwt_secrets)
        if success:
            self.stdout.write(
                self.style.SUCCESS('✓ JWT secrets stored')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to store JWT secrets')
            )
        
        # Redis secrets
        redis_secrets = {
            'url': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
            'password': os.getenv('REDIS_PASSWORD', ''),
            'max_connections': '50'
        }
        
        success = vault_client.store_secret('app/redis', redis_secrets)
        if success:
            self.stdout.write(
                self.style.SUCCESS('✓ Redis secrets stored')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to store Redis secrets')
            )
        
        # Blockchain RPC secrets
        blockchain_secrets = {
            'bitcoin_rpc_url': os.getenv('BITCOIN_RPC_URL', 'http://bitcoin-core:8332'),
            'bitcoin_rpc_user': os.getenv('BITCOIN_RPC_USER', 'bitcoin'),
            'bitcoin_rpc_password': os.getenv('BITCOIN_RPC_PASSWORD', 'password'),
            'ethereum_rpc_url': os.getenv('ETHEREUM_RPC_URL', 'http://geth:8545'),
            'cardano_rpc_url': os.getenv('CARDANO_RPC_URL', 'http://cardano-node:3001'),
            'polkadot_rpc_url': os.getenv('POLKADOT_RPC_URL', 'ws://polkadot-node:9944')
        }
        
        success = vault_client.store_secret('app/blockchain', blockchain_secrets)
        if success:
            self.stdout.write(
                self.style.SUCCESS('✓ Blockchain RPC secrets stored')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to store blockchain RPC secrets')
            )
        
        # Email/SMTP secrets
        email_secrets = {
            'smtp_host': os.getenv('SMTP_HOST', 'localhost'),
            'smtp_port': os.getenv('SMTP_PORT', '587'),
            'smtp_user': os.getenv('SMTP_USER', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@soundpesa.com')
        }
        
        success = vault_client.store_secret('app/email', email_secrets)
        if success:
            self.stdout.write(
                self.style.SUCCESS('✓ Email secrets stored')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to store email secrets')
            )