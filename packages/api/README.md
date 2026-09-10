# Sound Pesa API

Django REST API service providing blockchain transaction capabilities across Bitcoin, Ethereum, Cardano, and Polkadot networks.

## 🏗️ Architecture

The API follows Django's app-based architecture with the following components:

```
packages/api/
├── apps/
│   ├── authentication/    # User management and JWT auth
│   ├── wallets/          # Multi-chain wallet management
│   ├── transactions/     # Transaction processing engine
│   └── blockchain/       # Blockchain adapter interfaces
├── sound_pesa/          # Django project settings
└── manage.py           # Django management commands
```

## 🚀 Quick Start

### Local Development

1. **Set up Python environment:**
   ```bash
   cd packages/api
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Configure your database and blockchain connections
   ```

4. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver
   ```

### Docker Development

```bash
# From project root
docker-compose up api
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | User registration |
| POST | `/api/auth/login/` | User authentication |
| POST | `/api/auth/logout/` | Session termination |
| POST | `/api/auth/refresh/` | JWT token refresh |
| GET | `/api/user/profile/` | User profile data |

### Wallet Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wallets/` | List user wallets |
| POST | `/api/wallets/create/` | Create new wallet |
| GET | `/api/wallets/{chain}/balance/` | Get chain balance |
| GET | `/api/wallets/{chain}/history/` | Transaction history |

### Transaction Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/transactions/send/` | Send cryptocurrency |
| GET | `/api/transactions/{id}/` | Transaction details |
| GET | `/api/transactions/pending/` | Pending transactions |
| POST | `/api/transactions/estimate-fee/` | Fee estimation |

### Blockchain Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/blockchain/{chain}/status/` | Node sync status |
| GET | `/api/blockchain/{chain}/block-height/` | Current block info |

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/soundpesa
REDIS_URL=redis://localhost:6379/0

# Security Settings
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret
VAULT_URL=http://localhost:8200
VAULT_TOKEN=your-vault-token

# Blockchain Node Connections
BITCOIN_RPC_URL=http://localhost:8332
BITCOIN_RPC_USER=bitcoin
BITCOIN_RPC_PASSWORD=password

ETHEREUM_RPC_URL=http://localhost:8545
ETHEREUM_WS_URL=ws://localhost:8546

CARDANO_NODE_SOCKET=/opt/cardano/db/socket
CARDANO_NETWORK=mainnet

POLKADOT_WS_URL=ws://localhost:9944

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Blockchain Adapter Configuration

Each blockchain adapter can be configured through Django settings:

```python
# settings.py
BLOCKCHAIN_ADAPTERS = {
    'bitcoin': {
        'adapter_class': 'apps.blockchain.adapters.bitcoin.BitcoinAdapter',
        'rpc_url': os.getenv('BITCOIN_RPC_URL'),
        'rpc_user': os.getenv('BITCOIN_RPC_USER'),
        'rpc_password': os.getenv('BITCOIN_RPC_PASSWORD'),
        'network': 'mainnet',  # or 'testnet'
    },
    'ethereum': {
        'adapter_class': 'apps.blockchain.adapters.ethereum.EthereumAdapter',
        'rpc_url': os.getenv('ETHEREUM_RPC_URL'),
        'ws_url': os.getenv('ETHEREUM_WS_URL'),
        'network': 'mainnet',
    },
    # ... other chains
}
```

## 🔐 Security Features

### Authentication & Authorization

- **JWT Tokens**: Stateless authentication with refresh tokens
- **Multi-Factor Authentication**: TOTP and SMS-based 2FA
- **Rate Limiting**: Per-user and per-endpoint rate limits
- **CORS Configuration**: Secure cross-origin resource sharing

### Private Key Management

- **Vault Integration**: All private keys stored in HashiCorp Vault
- **Encryption at Rest**: Database-level encryption for sensitive data
- **Secure Key Generation**: Cryptographically secure random key generation

### API Security

```python
# Rate limiting example
@ratelimit(key='user', rate='10/m', method='POST')
def send_transaction(request):
    # Transaction processing logic
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.authentication
python manage.py test apps.wallets
python manage.py test apps.transactions

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Structure

```
apps/
├── authentication/
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_serializers.py
├── wallets/
│   └── tests/
│       ├── test_models.py
│       ├── test_services.py
│       └── test_views.py
└── transactions/
    └── tests/
        ├── test_models.py
        ├── test_tasks.py
        └── test_views.py
```

## 📊 Monitoring & Logging

### Metrics Collection

The API exposes Prometheus metrics at `/metrics/`:

- Request count and duration by endpoint
- Database query performance
- Blockchain adapter response times
- Celery task execution metrics

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "transaction_created",
    user_id=user.id,
    transaction_id=transaction.id,
    blockchain=transaction.blockchain,
    amount=str(transaction.amount)
)
```

## 🔄 Background Tasks

### Celery Workers

The API uses Celery for asynchronous task processing:

```bash
# Start Celery worker
celery -A sound_pesa worker -l info

# Start Celery beat scheduler
celery -A sound_pesa beat -l info

# Monitor tasks
celery -A sound_pesa flower
```

### Task Examples

```python
# Transaction confirmation monitoring
@shared_task
def monitor_transaction_confirmations():
    pending_transactions = Transaction.objects.filter(status='pending')
    for tx in pending_transactions:
        adapter = get_blockchain_adapter(tx.blockchain)
        confirmations = adapter.get_transaction_confirmations(tx.hash)
        if confirmations >= REQUIRED_CONFIRMATIONS[tx.blockchain]:
            tx.status = 'confirmed'
            tx.save()
```

## 🚀 Deployment

### Production Settings

```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['api.soundpesa.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 600,
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### Docker Production

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "sound_pesa.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check PostgreSQL connection
python manage.py dbshell

# Run migrations
python manage.py migrate --run-syncdb
```

**Blockchain Node Connection:**
```bash
# Test Bitcoin RPC
curl -u user:pass -d '{"jsonrpc":"1.0","id":"test","method":"getblockchaininfo","params":[]}' \
  -H 'content-type: text/plain;' http://localhost:8332/

# Test Ethereum RPC
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://localhost:8545
```

**Celery Task Issues:**
```bash
# Check Celery worker status
celery -A sound_pesa inspect active

# Purge failed tasks
celery -A sound_pesa purge
```

### Performance Optimization

- **Database Indexing**: Ensure proper indexes on frequently queried fields
- **Connection Pooling**: Use pgbouncer for PostgreSQL connections
- **Caching**: Implement Redis caching for frequently accessed data
- **Query Optimization**: Use select_related and prefetch_related for ORM queries

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Write comprehensive tests for new features
3. Update documentation for API changes
4. Use type hints for better code clarity
5. Follow Django best practices for models and views