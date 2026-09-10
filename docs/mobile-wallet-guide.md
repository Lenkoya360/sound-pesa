# Mobile Wallet Integration Guide

## Overview

Sound Pesa uses [rn-crypto-wallet](https://github.com/vinnyhoward/rn-crypto-wallet) as the mobile application instead of building from scratch. This provides a battle-tested, secure multi-chain wallet with significant time and cost savings.

## Quick Start

### Automated Setup (Recommended)

```bash
# Run the setup script
./scripts/setup-mobile-wallet.sh

# Or use Makefile
make setup-mobile
```

### Manual Setup

```bash
# Clone the wallet repository
cd packages
git clone git@github.com:vinnyhoward/rn-crypto-wallet.git app

# Configure environment
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

# Install dependencies
npm install
npm install ../shared
```

## Development

### Start Development Server

```bash
# Local development
cd packages/app
npx expo start

# With Docker
docker-compose -f docker-compose.dev.yml up app

# Using Makefile
make app-local
```

### Testing on Devices

**iOS:**

1. Install Expo Go from App Store
2. Run `npx expo start`
3. Scan QR code with Camera app

**Android:**

1. Install Expo Go from Play Store
2. Run `npx expo start`
3. Scan QR code with Expo Go app

**Physical Devices with API Access:**

```bash
# Use ngrok to expose local API
ngrok http 8000

# Update .env with ngrok URL
API_URL=https://your-ngrok-url.ngrok.io
EXPO_PUBLIC_API_URL=https://your-ngrok-url.ngrok.io
```

## API Integration

### Authentication

Create `packages/app/src/services/soundpesa-api.ts`:

```typescript
import axios from "axios";
import { getSecureItem, setSecureItem } from "./secure-storage";

const API_BASE_URL = process.env.API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const token = await getSecureItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = await getSecureItem("refresh_token");
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${API_BASE_URL}/api/auth/refresh/`,
            {
              refresh: refreshToken,
            },
          );
          await setSecureItem("auth_token", response.data.access);
          error.config.headers.Authorization = `Bearer ${response.data.access}`;
          return axios(error.config);
        } catch (refreshError) {
          // Redirect to login
          await setSecureItem("auth_token", "");
          await setSecureItem("refresh_token", "");
        }
      }
    }
    return Promise.reject(error);
  },
);

// API methods
export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/api/auth/login/", { email, password }),
  register: (data: any) => api.post("/api/auth/register/", data),
  logout: () => api.post("/api/auth/logout/"),
};

export const walletAPI = {
  list: () => api.get("/api/wallets/"),
  create: (blockchain: string) => api.post("/api/wallets/", { blockchain }),
  getBalance: (blockchain: string) =>
    api.get(`/api/wallets/${blockchain}/balance/`),
};

export const transactionAPI = {
  create: (data: any) => api.post("/api/transactions/create/", data),
  get: (id: string) => api.get(`/api/transactions/${id}/`),
  list: () => api.get("/api/transactions/"),
};
```

### WebSocket Integration

```typescript
// packages/app/src/services/websocket.ts
import { io, Socket } from "socket.io-client";

const WS_URL = process.env.WS_URL || "ws://localhost:8000/ws";

class WebSocketService {
  private socket: Socket | null = null;

  connect(token: string) {
    this.socket = io(WS_URL, {
      auth: { token },
      transports: ["websocket"],
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event: string, callback: (data: any) => void) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  emit(event: string, data: any) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export default new WebSocketService();
```

## Customization

### Branding

1. **App Name**: Update `packages/app/app.json`

```json
{
  "expo": {
    "name": "Sound Pesa",
    "slug": "sound-pesa"
  }
}
```

2. **App Icon**: Replace `packages/app/assets/icon.png`
3. **Splash Screen**: Replace `packages/app/assets/splash.png`
4. **Colors**: Update theme configuration in the wallet's theme files

### Custom Features

Add Sound Pesa-specific features:

- Peer-to-peer payments
- Contact management
- Payment requests
- Transaction notes
- Push notifications

## Testing

```bash
# Unit tests
cd packages/app
npm test

# E2E tests
npm run test:e2e

# Lint
npm run lint
```

## Building for Production

```bash
# iOS
npx expo build:ios

# Android
npx expo build:android

# Using EAS Build
eas build --platform ios
eas build --platform android
```

## Common Commands

```bash
# Setup
make setup-mobile              # Set up mobile wallet
./scripts/setup-mobile-wallet.sh  # Alternative setup

# Development
make app-local                 # Start locally
make app                       # Start in Docker
cd packages/app && npx expo start  # Direct start

# Testing
make test-app                  # Run tests
npm test                       # Direct test

# Utilities
npx expo start --clear         # Clear cache
npx expo start --ios           # iOS simulator
npx expo start --android       # Android emulator
npx expo start --tunnel        # Tunnel mode
```

## Troubleshooting

### Metro Bundler Issues

```bash
npx expo start --clear
rm -rf node_modules/.cache
```

### Port Already in Use

```bash
lsof -ti:19000 | xargs kill -9
npx expo start
```

### Cannot Connect to API

```bash
# Check API is running
curl http://localhost:8000/health/

# Use ngrok for physical devices
ngrok http 8000
```

### iOS Simulator Not Opening

```bash
open -a Simulator
npx expo start --ios
```

### Android Emulator Issues

```bash
emulator -list-avds
emulator -avd Pixel_4_API_30
npx expo start --android
```

## Integration Checklist

- [ ] Clone rn-crypto-wallet repository
- [ ] Configure environment variables
- [ ] Install dependencies
- [ ] Test basic setup
- [ ] Integrate authentication API
- [ ] Integrate wallet management API
- [ ] Integrate transaction API
- [ ] Set up WebSocket connection
- [ ] Customize branding
- [ ] Add custom features
- [ ] Write tests
- [ ] Test on iOS and Android
- [ ] Optimize performance
- [ ] Security audit
- [ ] Build for production
- [ ] Deploy to app stores

## Resources

- [rn-crypto-wallet Repository](https://github.com/vinnyhoward/rn-crypto-wallet)
- [React Native Documentation](https://reactnative.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [Sound Pesa API Documentation](http://localhost:8000/api/docs/)

## Support

For issues or questions:

1. Check this guide
2. Review [Troubleshooting](./troubleshooting.md)
3. Check rn-crypto-wallet repository issues
4. Create an issue in Sound Pesa repository
