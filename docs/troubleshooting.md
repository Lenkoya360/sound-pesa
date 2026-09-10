# Sound Pesa Platform Troubleshooting Guide

This guide provides solutions for common issues encountered during development, deployment, and operation of the Sound Pesa platform.

## Table of Contents

- [Development Environment Issues](#development-environment-issues)
- [Docker and Container Issues](#docker-and-container-issues)
- [Database Issues](#database-issues)
- [Blockchain Node Issues](#blockchain-node-issues)
- [API Service Issues](#api-service-issues)
- [Frontend Application Issues](#frontend-application-issues)
- [Authentication and Security Issues](#authentication-and-security-issues)
- [Performance Issues](#performance-issues)
- [Monitoring and Logging Issues](#monitoring-and-logging-issues)
- [Deployment Issues](#deployment-issues)

## Development Environment Issues

### Issue: Docker Compose Services Won't Start

**Symptoms:**
- Services fail to start with `docker-compose up`
- Port binding errors
- Container exit codes

**Solutions:**

1. **Check port conflicts:**
   ```bash
   # Check if ports are already in use
   netstat -tulpn | grep :8000
   lsof -i :8000
   
   # Kill processes using required ports
   sudo kill -9 $(lsof -t -i:8000)
   ```

2. **Clean Docker environment:**
   ```bash
   # Stop all containers
   docker-compose down
   
   # Remove all containers and volumes
   docker-compose down -v --remove-orphans
   
   # Clean Docker system
   docker system prune -a
   
   # Rebuild containers
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Check Docker resources:**
   ```bash
   # Increase Docker memory allocation (Docker Desktop)
   # Settings > Resources > Memory: 8GB+
   
   # Check available disk space
   df -h
   docker system df
   ```

### Issue: Hot Reload Not Working

**Symptoms:**
- Code changes not reflected in running containers
- Need to restart containers for changes

**Solutions:**

1. **Verify volume mounts:**
   ```yaml
   # docker-compose.dev.yml
   services:
     api:
       volumes:
         - ./packages/api:/app
         - /app/venv  # Exclude virtual environment
   ```

2. **Check file permissions:**
   ```bash
   # Fix file permissions (Linux/macOS)
   sudo chown -R $USER:$USER packages/
   chmod -R 755 packages/
   ```

3. **Restart development server:**
   ```bash
   # API hot reload
   docker-compose restart api
   
   # Web hot reload
   docker-compose restart web
   ```

### Issue: Environment Variables Not Loading

**Symptoms:**
- Configuration errors
- Services can't connect to dependencies
- Missing API keys or secrets

**Solutions:**

1. **Check .env file location:**
   ```bash
   # Ensure .env files exist
   ls -la .env*
   ls -la packages/*/env*
   
   # Copy from examples
   cp .env.example .env
   cp packages/api/.env.example packages/api/.env
   ```

2. **Validate environment variables:**
   ```bash
   # Check if variables are loaded
   docker-compose config
   
   # Debug specific service environment
   docker-compose exec api env | grep DATABASE
   ```

3. **Fix variable syntax:**
   ```bash
   # Correct format in .env files
   DATABASE_URL=postgresql://user:pass@localhost:5432/db
   # Not: DATABASE_URL = postgresql://user:pass@localhost:5432/db
   ```

## Docker and Container Issues

### Issue: Container Memory Issues

**Symptoms:**
- Containers being killed (exit code 137)
- Out of memory errors
- Slow performance

**Solutions:**

1. **Increase container memory limits:**
   ```yaml
   # docker-compose.yml
   services:
     api:
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

2. **Monitor memory usage:**
   ```bash
   # Check container memory usage
   docker stats
   
   # Check system memory
   free -h
   htop
   ```

3. **Optimize application memory:**
   ```python
   # Django settings for memory optimization
   DATABASES = {
       'default': {
           'CONN_MAX_AGE': 600,
           'OPTIONS': {
               'MAX_CONNS': 20,
           }
       }
   }
   ```

### Issue: Container Networking Problems

**Symptoms:**
- Services can't communicate with each other
- Connection refused errors
- DNS resolution failures

**Solutions:**

1. **Check Docker networks:**
   ```bash
   # List Docker networks
   docker network ls
   
   # Inspect network configuration
   docker network inspect sound-pesa_default
   
   # Test connectivity between containers
   docker-compose exec api ping postgres
   ```

2. **Use service names for internal communication:**
   ```python
   # Use Docker service names, not localhost
   DATABASE_URL = 'postgresql://user:pass@postgres:5432/db'
   REDIS_URL = 'redis://redis:6379/0'
   ```

3. **Recreate networks:**
   ```bash
   # Remove and recreate networks
   docker-compose down
   docker network prune
   docker-compose up
   ```

## Database Issues

### Issue: PostgreSQL Connection Errors

**Symptoms:**
- `psycopg2.OperationalError: could not connect to server`
- Database connection timeouts
- Authentication failures

**Solutions:**

1. **Check PostgreSQL service status:**
   ```bash
   # Check if PostgreSQL container is running
   docker-compose ps postgres
   
   # Check PostgreSQL logs
   docker-compose logs postgres
   
   # Connect to PostgreSQL directly
   docker-compose exec postgres psql -U soundpesa -d soundpesa
   ```

2. **Verify connection parameters:**
   ```bash
   # Test connection from API container
   docker-compose exec api python manage.py dbshell
   
   # Check environment variables
   docker-compose exec api env | grep DATABASE
   ```

3. **Reset database:**
   ```bash
   # Stop services
   docker-compose stop api celery-worker
   
   # Reset database
   docker-compose exec postgres psql -U soundpesa -c "DROP DATABASE IF EXISTS soundpesa;"
   docker-compose exec postgres psql -U soundpesa -c "CREATE DATABASE soundpesa;"
   
   # Run migrations
   docker-compose exec api python manage.py migrate
   ```

### Issue: Database Migration Errors

**Symptoms:**
- Migration conflicts
- Schema inconsistencies
- Foreign key constraint errors

**Solutions:**

1. **Check migration status:**
   ```bash
   # List migrations
   docker-compose exec api python manage.py showmigrations
   
   # Check for conflicts
   docker-compose exec api python manage.py makemigrations --dry-run
   ```

2. **Resolve migration conflicts:**
   ```bash
   # Merge migrations
   docker-compose exec api python manage.py makemigrations --merge
   
   # Fake apply problematic migration
   docker-compose exec api python manage.py migrate --fake app_name migration_name
   ```

3. **Reset migrations (development only):**
   ```bash
   # Remove migration files
   find packages/api/apps/*/migrations/ -name "*.py" -not -name "__init__.py" -delete
   
   # Create fresh migrations
   docker-compose exec api python manage.py makemigrations
   docker-compose exec api python manage.py migrate
   ```

## Blockchain Node Issues

### Issue: Bitcoin Core Sync Problems

**Symptoms:**
- Node not synchronizing
- RPC connection errors
- Slow sync progress

**Solutions:**

1. **Check Bitcoin Core status:**
   ```bash
   # Check Bitcoin Core logs
   docker-compose logs bitcoin-core
   
   # Check sync status
   docker-compose exec bitcoin-core bitcoin-cli getblockchaininfo
   
   # Check peer connections
   docker-compose exec bitcoin-core bitcoin-cli getpeerinfo
   ```

2. **Improve sync performance:**
   ```bash
   # Add more peers in bitcoin.conf
   addnode=seed.bitcoin.sipa.be
   addnode=dnsseed.bluematt.me
   addnode=dnsseed.bitcoin.dashjr.org
   
   # Increase database cache
   dbcache=2048
   ```

3. **Use blockchain snapshot (testnet):**
   ```bash
   # Download blockchain snapshot
   wget https://snapshots.bitcoin.org/testnet/latest.tar.gz
   
   # Extract to data directory
   docker-compose exec bitcoin-core tar -xzf latest.tar.gz -C /bitcoin/.bitcoin/
   ```

### Issue: Ethereum Node Sync Issues

**Symptoms:**
- Geth not syncing
- Beacon chain connection errors
- High memory usage

**Solutions:**

1. **Check Ethereum node status:**
   ```bash
   # Check Geth logs
   docker-compose logs geth
   
   # Check sync status
   docker-compose exec geth geth attach --exec "eth.syncing"
   
   # Check peer count
   docker-compose exec geth geth attach --exec "net.peerCount"
   ```

2. **Optimize Geth configuration:**
   ```bash
   # Use light sync mode for development
   --syncmode=light
   
   # Reduce cache size if memory limited
   --cache=1024
   
   # Enable snap sync
   --syncmode=snap
   ```

3. **Check Prysm beacon chain:**
   ```bash
   # Check beacon chain logs
   docker-compose logs prysm-beacon
   
   # Verify Geth connection
   docker-compose exec prysm-beacon curl http://geth:8545
   ```

### Issue: Cardano Node Connection Problems

**Symptoms:**
- Node not connecting to network
- Socket file errors
- Sync failures

**Solutions:**

1. **Check Cardano node status:**
   ```bash
   # Check node logs
   docker-compose logs cardano-node
   
   # Check socket file
   docker-compose exec cardano-node ls -la /opt/cardano/db/
   
   # Test node query
   docker-compose exec cardano-node cardano-cli query tip --mainnet
   ```

2. **Fix socket permissions:**
   ```bash
   # Ensure socket directory exists
   docker-compose exec cardano-node mkdir -p /opt/cardano/db
   
   # Fix permissions
   docker-compose exec cardano-node chown -R cardano:cardano /opt/cardano/db
   ```

3. **Update topology configuration:**
   ```json
   {
     "Producers": [
       {
         "addr": "relays-new.cardano-mainnet.iohk.io",
         "port": 3001,
         "valency": 2
       }
     ]
   }
   ```

## API Service Issues

### Issue: Django Server Errors

**Symptoms:**
- 500 Internal Server Error
- Import errors
- Module not found errors

**Solutions:**

1. **Check Django logs:**
   ```bash
   # View API logs
   docker-compose logs api
   
   # Follow logs in real-time
   docker-compose logs -f api
   
   # Check Django debug mode
   docker-compose exec api python manage.py shell -c "from django.conf import settings; print(settings.DEBUG)"
   ```

2. **Verify Python dependencies:**
   ```bash
   # Check installed packages
   docker-compose exec api pip list
   
   # Install missing packages
   docker-compose exec api pip install -r requirements.txt
   
   # Rebuild container if needed
   docker-compose build api
   ```

3. **Check Django configuration:**
   ```bash
   # Validate Django settings
   docker-compose exec api python manage.py check
   
   # Test database connection
   docker-compose exec api python manage.py dbshell
   
   # Collect static files
   docker-compose exec api python manage.py collectstatic --noinput
   ```

### Issue: Celery Worker Problems

**Symptoms:**
- Tasks not processing
- Worker connection errors
- Task failures

**Solutions:**

1. **Check Celery worker status:**
   ```bash
   # Check worker logs
   docker-compose logs celery-worker
   
   # Inspect active workers
   docker-compose exec celery-worker celery -A sound_pesa inspect active
   
   # Check queue status
   docker-compose exec celery-worker celery -A sound_pesa inspect reserved
   ```

2. **Restart Celery services:**
   ```bash
   # Restart workers
   docker-compose restart celery-worker celery-beat
   
   # Purge failed tasks
   docker-compose exec celery-worker celery -A sound_pesa purge
   ```

3. **Check RabbitMQ connection:**
   ```bash
   # Check RabbitMQ status
   docker-compose logs rabbitmq
   
   # Access RabbitMQ management UI
   # http://localhost:15672 (guest/guest)
   
   # Test connection
   docker-compose exec celery-worker python -c "from celery import Celery; app = Celery('sound_pesa'); print(app.control.inspect().stats())"
   ```

### Issue: API Authentication Errors

**Symptoms:**
- JWT token errors
- Authentication failures
- Permission denied errors

**Solutions:**

1. **Check JWT configuration:**
   ```bash
   # Verify JWT settings
   docker-compose exec api python manage.py shell -c "
   from django.conf import settings
   print('JWT_SECRET_KEY:', bool(settings.JWT_SECRET_KEY))
   print('JWT_ALGORITHM:', settings.JWT_ALGORITHM)
   "
   ```

2. **Test token generation:**
   ```bash
   # Create test user and token
   docker-compose exec api python manage.py shell -c "
   from django.contrib.auth import get_user_model
   from rest_framework_simplejwt.tokens import RefreshToken
   User = get_user_model()
   user = User.objects.create_user('test@example.com', 'password123')
   token = RefreshToken.for_user(user)
   print('Access Token:', str(token.access_token))
   "
   ```

3. **Check authentication middleware:**
   ```python
   # Verify middleware order in settings.py
   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       'django.middleware.security.SecurityMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.middleware.common.CommonMiddleware',
       'django.middleware.csrf.CsrfViewMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       # ... other middleware
   ]
   ```

## Frontend Application Issues

### Issue: Next.js Build Errors

**Symptoms:**
- Build failures
- TypeScript errors
- Module resolution errors

**Solutions:**

1. **Check build logs:**
   ```bash
   # Check web container logs
   docker-compose logs web
   
   # Build locally for debugging
   cd packages/web
   npm run build
   ```

2. **Fix TypeScript errors:**
   ```bash
   # Check TypeScript configuration
   cd packages/web
   npx tsc --noEmit
   
   # Update type definitions
   npm install --save-dev @types/node @types/react
   ```

3. **Clear Next.js cache:**
   ```bash
   # Clear Next.js cache
   cd packages/web
   rm -rf .next
   npm run build
   
   # Clear node_modules if needed
   rm -rf node_modules package-lock.json
   npm install
   ```

### Issue: React Native Metro Bundler Errors

**Symptoms:**
- Metro bundler crashes
- Module resolution failures
- Cache issues

**Solutions:**

1. **Clear Metro cache:**
   ```bash
   # Clear Metro cache
   cd packages/app
   npx expo start --clear
   
   # Reset Metro cache completely
   rm -rf node_modules/.cache
   npx expo start --clear
   ```

2. **Fix module resolution:**
   ```javascript
   // metro.config.js
   const { getDefaultConfig } = require('expo/metro-config');
   
   const config = getDefaultConfig(__dirname);
   
   // Add shared package to watchFolders
   config.watchFolders = [
     path.resolve(__dirname, '../shared'),
   ];
   
   module.exports = config;
   ```

3. **Check Expo configuration:**
   ```bash
   # Verify Expo configuration
   cd packages/app
   npx expo doctor
   
   # Update Expo CLI
   npm install -g @expo/cli@latest
   ```

### Issue: API Connection Errors from Frontend

**Symptoms:**
- CORS errors
- Network request failures
- API endpoint not found

**Solutions:**

1. **Check CORS configuration:**
   ```python
   # Django settings.py
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://127.0.0.1:3000",
   ]
   
   CORS_ALLOW_CREDENTIALS = True
   ```

2. **Verify API endpoints:**
   ```bash
   # Test API endpoint directly
   curl -X GET http://localhost:8000/api/health/
   
   # Check API documentation
   # http://localhost:8000/api/docs/
   ```

3. **Check network configuration:**
   ```javascript
   // Next.js - next.config.js
   module.exports = {
     async rewrites() {
       return [
         {
           source: '/api/:path*',
           destination: 'http://api:8000/api/:path*',
         },
       ];
     },
   };
   ```

## Authentication and Security Issues

### Issue: Vault Connection Errors

**Symptoms:**
- Vault service unavailable
- Authentication failures
- Secret retrieval errors

**Solutions:**

1. **Check Vault status:**
   ```bash
   # Check Vault container
   docker-compose logs vault
   
   # Check Vault status
   docker-compose exec vault vault status
   
   # Initialize Vault (first time only)
   docker-compose exec vault vault operator init
   ```

2. **Unseal Vault:**
   ```bash
   # Unseal Vault with keys
   docker-compose exec vault vault operator unseal <key1>
   docker-compose exec vault vault operator unseal <key2>
   docker-compose exec vault vault operator unseal <key3>
   
   # Authenticate with root token
   docker-compose exec vault vault auth <root-token>
   ```

3. **Configure Vault policies:**
   ```bash
   # Create policy for API service
   docker-compose exec vault vault policy write api-policy - <<EOF
   path "secret/data/api/*" {
     capabilities = ["read"]
   }
   EOF
   
   # Create token for API service
   docker-compose exec vault vault token create -policy=api-policy
   ```

### Issue: Two-Factor Authentication Problems

**Symptoms:**
- TOTP code validation failures
- QR code generation errors
- Backup code issues

**Solutions:**

1. **Check TOTP configuration:**
   ```python
   # Verify TOTP settings
   TOTP_ISSUER_NAME = 'Sound Pesa'
   TOTP_TOKEN_VALIDITY = 30  # seconds
   ```

2. **Test TOTP generation:**
   ```bash
   # Test TOTP in Django shell
   docker-compose exec api python manage.py shell -c "
   from django_otp.plugins.otp_totp.models import TOTPDevice
   from django.contrib.auth import get_user_model
   User = get_user_model()
   user = User.objects.first()
   device = TOTPDevice.objects.create(user=user, name='test')
   print('Secret:', device.bin_key.hex())
   print('QR URL:', device.config_url)
   "
   ```

3. **Synchronize time:**
   ```bash
   # Ensure system time is synchronized
   sudo ntpdate -s time.nist.gov
   
   # Check container time
   docker-compose exec api date
   ```

## Performance Issues

### Issue: Slow API Response Times

**Symptoms:**
- High response times
- Timeout errors
- Poor user experience

**Solutions:**

1. **Profile API performance:**
   ```bash
   # Enable Django debug toolbar
   pip install django-debug-toolbar
   
   # Add to INSTALLED_APPS and MIDDLEWARE
   
   # Use Django silk for profiling
   pip install django-silk
   ```

2. **Optimize database queries:**
   ```python
   # Use select_related for foreign keys
   wallets = Wallet.objects.select_related('user').all()
   
   # Use prefetch_related for many-to-many
   users = User.objects.prefetch_related('wallets').all()
   
   # Add database indexes
   class Meta:
       indexes = [
           models.Index(fields=['user', 'blockchain']),
           models.Index(fields=['created_at']),
       ]
   ```

3. **Implement caching:**
   ```python
   # Cache expensive operations
   from django.core.cache import cache
   
   def get_wallet_balance(wallet_id):
       cache_key = f'wallet_balance_{wallet_id}'
       balance = cache.get(cache_key)
       if balance is None:
           balance = fetch_balance_from_blockchain(wallet_id)
           cache.set(cache_key, balance, timeout=300)
       return balance
   ```

### Issue: High Memory Usage

**Symptoms:**
- Containers being killed
- Swap usage
- System slowdown

**Solutions:**

1. **Monitor memory usage:**
   ```bash
   # Check container memory usage
   docker stats --no-stream
   
   # Check system memory
   free -h
   htop
   
   # Check Django memory usage
   pip install memory-profiler
   ```

2. **Optimize Django settings:**
   ```python
   # Reduce database connection pool
   DATABASES = {
       'default': {
           'CONN_MAX_AGE': 600,
           'OPTIONS': {
               'MAX_CONNS': 20,
           }
       }
   }
   
   # Optimize logging
   LOGGING = {
       'handlers': {
           'file': {
               'level': 'INFO',  # Reduce log level
               'maxBytes': 1024*1024*15,  # 15MB
               'backupCount': 10,
           }
       }
   }
   ```

3. **Implement pagination:**
   ```python
   # Use pagination for large datasets
   from rest_framework.pagination import PageNumberPagination
   
   class StandardResultsSetPagination(PageNumberPagination):
       page_size = 20
       page_size_query_param = 'page_size'
       max_page_size = 100
   ```

## Monitoring and Logging Issues

### Issue: Prometheus Metrics Not Collecting

**Symptoms:**
- Missing metrics in Grafana
- Prometheus targets down
- Scrape errors

**Solutions:**

1. **Check Prometheus configuration:**
   ```bash
   # Check Prometheus logs
   docker-compose logs prometheus
   
   # Verify Prometheus targets
   # http://localhost:9090/targets
   
   # Check configuration
   docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
   ```

2. **Verify metrics endpoints:**
   ```bash
   # Test metrics endpoints
   curl http://localhost:8000/metrics
   curl http://localhost:9090/metrics
   
   # Check if services expose metrics
   docker-compose exec api python manage.py shell -c "
   import requests
   response = requests.get('http://localhost:8000/metrics')
   print(response.status_code, len(response.text))
   "
   ```

3. **Fix service discovery:**
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'django-api'
       static_configs:
         - targets: ['api:8000']  # Use service name, not localhost
   ```

### Issue: Grafana Dashboard Not Loading

**Symptoms:**
- Dashboard shows no data
- Data source connection errors
- Query errors

**Solutions:**

1. **Check Grafana data sources:**
   ```bash
   # Check Grafana logs
   docker-compose logs grafana
   
   # Access Grafana UI
   # http://localhost:3001 (admin/admin)
   
   # Test Prometheus connection
   curl -X GET http://prometheus:9090/api/v1/query?query=up
   ```

2. **Verify dashboard configuration:**
   ```bash
   # Check dashboard provisioning
   docker-compose exec grafana ls -la /etc/grafana/provisioning/dashboards/
   
   # Validate JSON syntax
   docker-compose exec grafana cat /etc/grafana/provisioning/dashboards/dashboard.json | jq .
   ```

3. **Fix data source configuration:**
   ```yaml
   # datasources/prometheus.yml
   datasources:
     - name: Prometheus
       type: prometheus
       url: http://prometheus:9090  # Use service name
       access: proxy
       isDefault: true
   ```

## Deployment Issues

### Issue: Production Deployment Failures

**Symptoms:**
- Services fail to start in production
- Configuration errors
- Resource constraints

**Solutions:**

1. **Check production configuration:**
   ```bash
   # Validate production compose file
   docker-compose -f docker-compose.prod.yml config
   
   # Check environment variables
   docker-compose -f docker-compose.prod.yml exec api env
   ```

2. **Verify resource allocation:**
   ```yaml
   # docker-compose.prod.yml
   services:
     api:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
           reservations:
             cpus: '1'
             memory: 2G
   ```

3. **Check SSL/TLS configuration:**
   ```bash
   # Verify SSL certificates
   openssl x509 -in /path/to/cert.pem -text -noout
   
   # Test SSL connection
   openssl s_client -connect yourdomain.com:443
   ```

### Issue: Database Migration Failures in Production

**Symptoms:**
- Migration errors during deployment
- Data integrity issues
- Downtime during migrations

**Solutions:**

1. **Test migrations in staging:**
   ```bash
   # Create staging database backup
   pg_dump -h staging-db -U user dbname > staging_backup.sql
   
   # Test migrations on copy
   docker-compose -f docker-compose.staging.yml exec api python manage.py migrate --dry-run
   ```

2. **Use zero-downtime migrations:**
   ```python
   # Add new column as nullable first
   class Migration(migrations.Migration):
       operations = [
           migrations.AddField(
               model_name='wallet',
               name='new_field',
               field=models.CharField(max_length=100, null=True),
           ),
       ]
   
   # Populate data in separate migration
   # Make field non-nullable in third migration
   ```

3. **Implement migration rollback plan:**
   ```bash
   # Create database backup before migration
   pg_dump -h prod-db -U user dbname > pre_migration_backup.sql
   
   # Test rollback procedure
   docker-compose exec api python manage.py migrate app_name previous_migration
   ```

## Getting Help

### Log Collection for Support

When reporting issues, collect relevant logs:

```bash
# Collect all service logs
docker-compose logs > all_services.log

# Collect specific service logs
docker-compose logs api > api.log
docker-compose logs postgres > postgres.log

# System information
docker version > system_info.txt
docker-compose version >> system_info.txt
uname -a >> system_info.txt
```

### Health Check Commands

Use these commands to verify system health:

```bash
# Check all services status
docker-compose ps

# Test API health endpoint
curl http://localhost:8000/api/health/

# Check database connectivity
docker-compose exec api python manage.py dbshell -c "SELECT 1;"

# Verify blockchain node connectivity
docker-compose exec api python manage.py shell -c "
from apps.blockchain.services import BlockchainService
service = BlockchainService()
print('Bitcoin:', service.get_blockchain_status('bitcoin'))
"
```

### Performance Monitoring

Monitor system performance:

```bash
# Container resource usage
docker stats

# System resource usage
htop
iotop
nethogs

# Database performance
docker-compose exec postgres pg_stat_activity

# API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/wallets/
```

For additional support, check the project documentation or create an issue in the repository with detailed logs and system information.