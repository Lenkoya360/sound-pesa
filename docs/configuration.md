# Sound Pesa Platform Configuration Guide

This guide provides comprehensive information about configuring the Sound Pesa platform for different environments.

## Table of Contents

- [Overview](#overview)
- [Environment Files](#environment-files)
- [Configuration Variables](#configuration-variables)
- [Environment-Specific Settings](#environment-specific-settings)
- [Security Configuration](#security-configuration)
- [Validation and Testing](#validation-and-testing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Sound Pesa platform uses environment-based configuration to manage settings across different deployment environments. Configuration is managed through environment files (`.env`) and Docker Compose files.

### Configuration Hierarchy

```
Root Configuration
├── .env.example (template)
├── .env.development (development settings)
├── .env.staging (staging settings)
├── .env.production (production settings)
└── Package-Specific Configuration
    ├── packages/api/.env.example
    ├── packages/web/.env.example
    └── packages/app/.env.example
```

## Environment Files

### Main Environment Files

| File | Purpose | Usage |
|------|---------|-------|
| `.env.example` | Template with all variables | Copy to create environment-specific files |
| `.env.development` | Development settings | Local development and testing |
| `.env.staging` | Staging settings | Pre-production testing |
| `.env.production` | Production settings | Live production deployment |

### Package-Specific Files

Each package has its own environment configuration:

- **API Package**: `packages/api/.env.example`
- **Web Package**: `packages/web/.env.example`
- **Mobile App**: `packages/app/.env.example`

## Configuration Variables

### Project Configuration

```bash
# Project identification
COMPOSE_PROJECT_NAME=sound-pesa
ENVIRONMENT=development

# Used for Docker Compose service naming and isolation
```

### Database Configuration

```bash
# PostgreSQL settings
POSTGRES_DB=soundpesa
POSTGRES_USER=soundpesa
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Connection URL (auto-constructed)
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

**Important Notes:**
- Use strong passwords (minimum 12 characters)
- Different databases for each environment
- Connection pooling configured in API settings

### Redis Configuration

```bash
# Redis cache and session store
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_redis_password
REDIS_DB=0

# Multiple Redis databases for different purposes
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
REDIS_CACHE_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/1
REDIS_SESSION_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/2
```

### Message Queue Configuration

```bash
# RabbitMQ for Celery
RABBITMQ_DEFAULT_USER=soundpesa
RABBITMQ_DEFAULT_PASS=secure_rabbitmq_password
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672

# Celery configuration
CELERY_BROKER_URL=amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@${RABBITMQ_HOST}:${RABBITMQ_PORT}//
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/3
```

### Vault Configuration

```bash
# HashiCorp Vault for secrets management
VAULT_HOST=vault
VAULT_PORT=8200
VAULT_SCHEME=http  # Use https in production
VAULT_URL=${VAULT_SCHEME}://${VAULT_HOST}:${VAULT_PORT}

# Development settings (DO NOT use in production)
VAULT_DEV_ROOT_TOKEN_ID=dev-root-token
VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200

# Production settings
VAULT_TOKEN=your-production-vault-token
VAULT_ROLE_ID=your-vault-role-id
VAULT_SECRET_ID=your-vault-secret-id
```

### API Configuration

```bash
# Django core settings
DJANGO_SECRET_KEY=very-long-random-secret-key-here
DJANGO_DEBUG=false  # Always false in production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api,yourdomain.com

# JWT authentication
JWT_SECRET_KEY=secure-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=3600    # 1 hour
JWT_REFRESH_TOKEN_LIFETIME=86400  # 24 hours

# CORS settings
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS=true
```

### Blockchain Configuration

```bash
# Bitcoin Core
BITCOIN_NETWORK=mainnet  # or testnet for development
BITCOIN_RPC_HOST=bitcoin-core
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=bitcoin
BITCOIN_RPC_PASSWORD=secure_bitcoin_password
BITCOIN_RPC_URL=http://${BITCOIN_RPC_USER}:${BITCOIN_RPC_PASSWORD}@${BITCOIN_RPC_HOST}:${BITCOIN_RPC_PORT}

# Ethereum
ETHEREUM_NETWORK=mainnet  # or goerli for development
ETHEREUM_RPC_HOST=geth
ETHEREUM_RPC_PORT=8545
ETHEREUM_WS_PORT=8546
ETHEREUM_RPC_URL=http://${ETHEREUM_RPC_HOST}:${ETHEREUM_RPC_PORT}
ETHEREUM_WS_URL=ws://${ETHEREUM_RPC_HOST}:${ETHEREUM_WS_PORT}

# Cardano
CARDANO_NETWORK=mainnet  # or testnet for development
CARDANO_NODE_HOST=cardano-node
CARDANO_NODE_PORT=3001
CARDANO_NODE_SOCKET=/opt/cardano/db/socket

# Polkadot
POLKADOT_NETWORK=polkadot  # or westend for development
POLKADOT_WS_HOST=polkadot
POLKADOT_WS_PORT=9944
POLKADOT_WS_URL=ws://${POLKADOT_WS_HOST}:${POLKADOT_WS_PORT}
```

### Monitoring Configuration

```bash
# Prometheus metrics collection
PROMETHEUS_HOST=prometheus
PROMETHEUS_PORT=9090
PROMETHEUS_URL=http://${PROMETHEUS_HOST}:${PROMETHEUS_PORT}

# Grafana dashboards
GRAFANA_HOST=grafana
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_grafana_password
GRAFANA_URL=http://${GRAFANA_HOST}:${GRAFANA_PORT}

# Loki logging
LOKI_HOST=loki
LOKI_PORT=3100
LOKI_URL=http://${LOKI_HOST}:${LOKI_PORT}

# AlertManager
ALERTMANAGER_HOST=alertmanager
ALERTMANAGER_PORT=9093
ALERTMANAGER_URL=http://${ALERTMANAGER_HOST}:${ALERTMANAGER_PORT}
```

## Environment-Specific Settings

### Development Environment

**Characteristics:**
- Debug mode enabled
- Relaxed security settings
- Testnet blockchain connections
- Local service URLs
- Detailed logging

**Key Settings:**
```bash
ENVIRONMENT=development
DJANGO_DEBUG=true
LOG_LEVEL=DEBUG
BITCOIN_NETWORK=testnet
ETHEREUM_NETWORK=goerli
SECURE_SSL_REDIRECT=false
ENABLE_2FA=false  # Optional for easier testing
```

### Staging Environment

**Characteristics:**
- Production-like configuration
- Testnet blockchain connections
- SSL/TLS enabled
- Comprehensive monitoring
- Performance testing ready

**Key Settings:**
```bash
ENVIRONMENT=staging
DJANGO_DEBUG=false
LOG_LEVEL=INFO
BITCOIN_NETWORK=testnet
ETHEREUM_NETWORK=goerli
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
ENABLE_2FA=true
```

### Production Environment

**Characteristics:**
- Maximum security settings
- Mainnet blockchain connections
- SSL/TLS required
- Comprehensive monitoring and alerting
- Optimized performance settings

**Key Settings:**
```bash
ENVIRONMENT=production
DJANGO_DEBUG=false
LOG_LEVEL=WARNING
BITCOIN_NETWORK=mainnet
ETHEREUM_NETWORK=mainnet
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_PRELOAD=true
ENABLE_2FA=true
ENABLE_RATE_LIMITING=true
```

## Security Configuration

### Password Requirements

All passwords and secrets must meet these requirements:

1. **Minimum Length**: 12 characters (32+ recommended for production)
2. **Complexity**: Mix of uppercase, lowercase, numbers, and symbols
3. **Uniqueness**: Different for each service and environment
4. **No Common Patterns**: Avoid dictionary words, sequential characters

### Critical Security Variables

```bash
# These MUST be changed from defaults:
DJANGO_SECRET_KEY=          # Django cryptographic signing
JWT_SECRET_KEY=             # JWT token signing
POSTGRES_PASSWORD=          # Database access
REDIS_PASSWORD=             # Cache access
VAULT_TOKEN=                # Secrets management
NEXTAUTH_SECRET=            # Web authentication
```

### Production Security Checklist

- [ ] All default passwords changed
- [ ] SSL/TLS enabled (`SECURE_SSL_REDIRECT=true`)
- [ ] HSTS configured (`SECURE_HSTS_SECONDS=31536000`)
- [ ] Debug mode disabled (`DJANGO_DEBUG=false`)
- [ ] Secure cookies enabled (`SESSION_COOKIE_SECURE=true`)
- [ ] CSRF protection configured
- [ ] Rate limiting enabled
- [ ] Proper CORS origins set
- [ ] Vault properly configured and sealed
- [ ] Monitoring and alerting active

### SSL/TLS Configuration

```bash
# Production SSL settings
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true
SECURE_REFERRER_POLICY=strict-origin-when-cross-origin

# Cookie security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
CSRF_COOKIE_SECURE=true
CSRF_COOKIE_HTTPONLY=true
```

## Feature Flags

Control platform features through environment variables:

### Authentication Features
```bash
ENABLE_2FA=true                    # Two-factor authentication
ENABLE_EMAIL_VERIFICATION=true     # Email verification for registration
ENABLE_BIOMETRIC_AUTH=true         # Biometric authentication (mobile)
```

### Blockchain Features
```bash
ENABLE_BITCOIN=true                # Bitcoin support
ENABLE_ETHEREUM=true               # Ethereum support
ENABLE_CARDANO=true                # Cardano support
ENABLE_POLKADOT=true               # Polkadot support
```

### Platform Features
```bash
ENABLE_NOTIFICATIONS=true          # Push notifications
ENABLE_ANALYTICS=false             # Usage analytics
ENABLE_RATE_LIMITING=true          # API rate limiting
ENABLE_KYC=true                    # Know Your Customer verification
```

## Validation and Testing

### Configuration Validation Script

Use the provided validation script to check your configuration:

```bash
# Validate development configuration
./scripts/validate-config.sh development

# Validate production configuration with report
./scripts/validate-config.sh production --report
```

### Manual Validation Checklist

1. **File Existence**: All required `.env` files exist
2. **Variable Completeness**: All required variables are set
3. **Password Strength**: No weak or default passwords
4. **URL Formats**: All URLs are properly formatted
5. **Network Settings**: Appropriate networks for environment
6. **Security Settings**: Production security measures enabled
7. **Feature Flags**: Appropriate features enabled/disabled

### Testing Configuration

```bash
# Test Docker Compose configuration
docker-compose -f docker-compose.production.yml config

# Test environment variable loading
docker-compose -f docker-compose.production.yml exec api env | grep DATABASE

# Test service connectivity
docker-compose -f docker-compose.production.yml exec api python manage.py check
```

## Best Practices

### 1. Environment Separation

- **Never** use production credentials in development
- Use different databases for each environment
- Separate monitoring and logging per environment
- Use appropriate blockchain networks (testnet vs mainnet)

### 2. Secret Management

- Store secrets in HashiCorp Vault when possible
- Use environment variables for configuration
- Never commit `.env` files to version control
- Rotate secrets regularly (quarterly recommended)
- Use different secrets for each environment

### 3. Configuration Management

- Keep `.env.example` files up to date
- Document all configuration variables
- Use validation scripts before deployment
- Version control configuration templates
- Maintain environment-specific documentation

### 4. Security Practices

- Enable all security headers in production
- Use strong, unique passwords for all services
- Enable SSL/TLS for all external communications
- Configure proper CORS origins
- Enable rate limiting and DDoS protection
- Regular security audits of configuration

### 5. Monitoring and Logging

- Configure appropriate log levels for each environment
- Set up alerting for configuration-related issues
- Monitor configuration drift
- Log configuration changes
- Regular backup of configuration

## Troubleshooting

### Common Configuration Issues

#### 1. Service Connection Failures

**Problem**: Services can't connect to each other
**Solution**: 
- Check service names in Docker Compose
- Verify network configuration
- Ensure ports are correctly mapped
- Check firewall rules

#### 2. Authentication Failures

**Problem**: JWT or database authentication fails
**Solution**:
- Verify secret keys are correctly set
- Check password complexity
- Ensure no trailing spaces in variables
- Validate URL formats

#### 3. SSL/TLS Issues

**Problem**: HTTPS not working or certificate errors
**Solution**:
- Verify SSL certificate paths
- Check domain configuration
- Ensure SSL redirect is properly configured
- Validate certificate expiration

#### 4. Blockchain Connection Issues

**Problem**: Cannot connect to blockchain nodes
**Solution**:
- Verify RPC URLs and credentials
- Check network settings (mainnet vs testnet)
- Ensure blockchain nodes are synced
- Validate port configurations

### Configuration Debugging

```bash
# Check environment variable loading
docker-compose exec api python -c "import os; print(os.getenv('DATABASE_URL'))"

# Validate Django configuration
docker-compose exec api python manage.py check --deploy

# Test database connection
docker-compose exec api python manage.py dbshell

# Check Redis connection
docker-compose exec redis redis-cli ping

# Validate Vault connection
docker-compose exec vault vault status
```

### Environment Variable Precedence

1. Docker Compose environment section
2. `.env` file in project root
3. System environment variables
4. Default values in application code

### Getting Help

If you encounter configuration issues:

1. Run the configuration validation script
2. Check the troubleshooting guide
3. Review Docker Compose logs
4. Verify all required files exist
5. Check for typos in variable names
6. Ensure proper file permissions

For additional support, refer to the main troubleshooting documentation or create an issue with:
- Environment type (development/staging/production)
- Configuration validation report
- Relevant log excerpts
- Steps to reproduce the issue