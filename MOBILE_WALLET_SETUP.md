# Mobile Wallet Setup

Quick guide to set up [rn-crypto-wallet](https://github.com/vinnyhoward/rn-crypto-wallet) as the Sound Pesa mobile app.

## Quick Setup

```bash
# Automated setup (recommended)
./scripts/setup-mobile-wallet.sh

# Or use Makefile
make setup-mobile
```

## Manual Setup

```bash
# 1. Clone the wallet
cd packages
git clone git@github.com:vinnyhoward/rn-crypto-wallet.git app

# 2. Configure environment
cd app
cat > .env << 'EOF'
API_URL=http://localhost:8000
WS_URL=ws://localhost:8000/ws
BITCOIN_RPC_URL=http://localhost:8332
ETHEREUM_RPC_URL=http://localhost:8545
CARDANO_RPC_URL=http://localhost:3001
POLKADOT_RPC_URL=ws://localhost:9944
APP_NAME=Sound Pesa
APP_VERSION=1.0.0
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_DEV_MODE=true
EOF

# 3. Install dependencies
npm install
npm install ../shared
```

## Running the App

```bash
# Start API first
docker-compose -f docker-compose.dev.yml up api postgres redis

# Start mobile app
cd packages/app
npx expo start

# Or use simulators
npx expo start --ios      # iOS Simulator
npx expo start --android  # Android Emulator

# Or with Docker
docker-compose -f docker-compose.dev.yml up app
```

### Testing on Physical Devices

1. Install Expo Go (App Store/Play Store)
2. Run `npx expo start`
3. Scan QR code with device

## API Connection

For physical devices, use ngrok:

```bash
# Install and start ngrok
brew install ngrok
ngrok http 8000

# Update .env with ngrok URL
API_URL=https://your-ngrok-url.ngrok.io
EXPO_PUBLIC_API_URL=https://your-ngrok-url.ngrok.io
```

## Customization

1. **Branding**: Update `app.json`, replace icons in `assets/`
2. **API Integration**: See [Mobile Wallet Guide](./docs/mobile-wallet-guide.md)
3. **Custom Features**: Add Sound Pesa-specific functionality

## Common Commands

```bash
# Development
npx expo start              # Start dev server
npx expo start --clear      # Clear cache
npx expo start --ios        # iOS simulator
npx expo start --android    # Android emulator

# Testing
npm test                    # Run tests
npm run lint               # Lint code

# Building
npx expo build:ios         # Build iOS
npx expo build:android     # Build Android
```

## Troubleshooting

| Issue                    | Solution                          |
| ------------------------ | --------------------------------- |
| Metro bundler issues     | `npx expo start --clear`          |
| Port in use              | `lsof -ti:19000 \| xargs kill -9` |
| Can't connect to API     | Check API is running, use ngrok   |
| iOS simulator won't open | `open -a Simulator`               |

## Next Steps

1. Review [Mobile Wallet Guide](./docs/mobile-wallet-guide.md) for detailed integration
2. Customize branding and UI
3. Integrate Sound Pesa API
4. Add custom features
5. Test and deploy

## Resources

- [Mobile Wallet Guide](./docs/mobile-wallet-guide.md) - Detailed integration guide
- [rn-crypto-wallet](https://github.com/vinnyhoward/rn-crypto-wallet) - Source repository
- [Expo Docs](https://docs.expo.dev/) - Expo documentation
- [API Docs](http://localhost:8000/api/docs/) - Sound Pesa API
