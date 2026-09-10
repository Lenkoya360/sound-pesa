# Sound Pesa Platform

A fully containerized monorepo cryptocurrency platform enabling secure peer-to-peer transactions across Bitcoin, Ethereum, Cardano, and Polkadot networks.

## 🏗️ Architecture Overview

Sound Pesa follows a microservices architecture with Docker orchestration, implementing clean separation between frontend applications, API services, blockchain infrastructure, and shared utilities.

The mobile application uses [rn-crypto-wallet](https://github.com/vinnyhoward/rn-crypto-wallet) as the base implementation. See [Mobile Wallet Setup](./MOBILE_WALLET_SETUP.md) for details.

```
┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │ rn-crypto-wallet│
│   Application   │    │   Mobile App    │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
            ┌────────▼────────┐
            │  Nginx Proxy    │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  Django REST    │
            │      API        │
            └────────┬────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌──────▼──────┐    ┌────▼────┐
│Bitcoin│    │  Ethereum   │    │ Cardano │
│ Core  │    │Geth + Prysm │    │  Node   │
└───────┘    └─────────────┘    └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Node.js 18+ (for development)
- Python 3.11+ (for API development)

### Local Development Setup

1. **Clone the repository:**

   ```bash
   git clone git@github.com:Codechi-Ltd/sound-pesa.git
   cd sound-pesa
   ```

2. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment:**

   ```bash
   ./scripts/dev-setup.sh
   ```

4. **Access the applications:**
   - Web App: http://localhost:3000
   - API Documentation: http://localhost:8000/api/docs/
   - Grafana Dashboard: http://localhost:3001
   - Admin Panel: http://localhost:8000/admin/

## 📦 Package Structure

```
sound-pesa-platform/
├── packages/
│   ├── api/          # Django REST API
│   ├── web/          # Next.js web application
│   ├── app/          # rn-crypto-wallet (mobile app)
│   └── shared/       # Shared utilities and types
├── docker/           # Docker configurations
├── scripts/          # Development and deployment scripts
└── .kiro/           # Kiro specifications and documentation
```

### Mobile Application

The mobile app uses [rn-crypto-wallet](https://github.com/vinnyhoward/rn-crypto-wallet). Quick setup:

```bash
# Automated setup
make setup-mobile

# Or manual setup
./scripts/setup-mobile-wallet.sh
```

See [Mobile Wallet Setup Guide](./MOBILE_WALLET_SETUP.md) for detailed instructions.

## 🔧 Development

### API Development

```bash
cd packages/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

### Web Development

```bash
cd packages/web
npm install
npm run dev
```

### Mobile Development

The mobile app uses [rn-crypto-wallet](https://github.com/vinnyhoward/rn-crypto-wallet) as the base wallet implementation.

```bash
# First time setup - clone the wallet repository
cd packages
git clone git@github.com:vinnyhoward/rn-crypto-wallet.git app

# Or if using submodules
git submodule update --init --recursive

# Install dependencies and start
cd app
npm install
npx expo start
```

See [Mobile Wallet Setup](./MOBILE_WALLET_SETUP.md) for detailed setup instructions.

## 🐳 Docker Services

| Service      | Port  | Description                     |
| ------------ | ----- | ------------------------------- |
| api          | 8000  | Django REST API                 |
| web          | 3000  | Next.js web application         |
| app          | 19006 | React Native development server |
| postgres     | 5432  | PostgreSQL database             |
| redis        | 6379  | Redis cache and message broker  |
| bitcoin-core | 8332  | Bitcoin RPC interface           |
| geth         | 8545  | Ethereum JSON-RPC               |
| cardano-node | 3001  | Cardano node interface          |
| polkadot     | 9944  | Polkadot WebSocket              |
| prometheus   | 9090  | Metrics collection              |
| grafana      | 3001  | Monitoring dashboards           |
| vault        | 8200  | Secrets management              |

## 🔐 Security Features

- **Multi-Factor Authentication**: TOTP and SMS-based 2FA
- **Hardware Security Module**: Private key protection
- **Vault Integration**: Encrypted secrets management
- **Rate Limiting**: DDoS protection on all endpoints
- **Audit Logging**: Comprehensive transaction trails

## 🌐 Supported Blockchains

- **Bitcoin**: Native BTC transactions
- **Ethereum**: ETH and ERC-20 token support
- **Cardano**: ADA transactions and native tokens
- **Polkadot**: DOT transfers and staking

## 📊 Monitoring

The platform includes comprehensive monitoring with:

- **Prometheus**: Metrics collection
- **Grafana**: Visual dashboards
- **Loki**: Centralized logging
- **AlertManager**: Automated alerting

## 🧪 Testing

```bash
# Run all tests
./scripts/run-tests.sh

# API tests
cd packages/api && python manage.py test

# Web tests
cd packages/web && npm test

# Mobile tests
cd packages/app && npm test
```

## 📚 Documentation

### General Documentation

- [API Documentation](./packages/api/README.md)
- [Web Application Guide](./packages/web/README.md)
- [Deployment Guide](./docs/deployment.md)
- [Troubleshooting](./docs/troubleshooting.md)

### Mobile Wallet Documentation

- [Mobile Wallet Setup](./MOBILE_WALLET_SETUP.md) - Quick start guide
- [Mobile Wallet Guide](./docs/mobile-wallet-guide.md) - Detailed integration guide
- [rn-crypto-wallet Repository](https://github.com/vinnyhoward/rn-crypto-wallet) - Source code

## 🚀 Deployment

### Production Deployment

```bash
./scripts/deploy-prod.sh
```

### Staging Deployment

```bash
./scripts/deploy-staging.sh
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the [troubleshooting guide](./docs/troubleshooting.md)
- Review the [API documentation](./packages/api/README.md)
