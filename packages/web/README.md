# Sound Pesa Web Application

Next.js web application providing a responsive interface for multi-chain cryptocurrency transactions and wallet management.

## 🏗️ Architecture

The web application is built with Next.js 14+ using the App Router and follows modern React patterns:

```
packages/web/
├── app/                 # Next.js App Router pages
│   ├── auth/           # Authentication pages
│   ├── dashboard/      # Main wallet dashboard
│   └── profile/        # User profile management
├── components/         # Reusable React components
│   ├── ui/            # Base UI components
│   └── wallet/        # Wallet-specific components
├── contexts/          # React Context providers
├── hooks/             # Custom React hooks
├── lib/               # Utility functions and API clients
└── public/            # Static assets and PWA files
```

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   cd packages/web
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Configure API endpoints and other settings
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Access the application:**
   - Development: http://localhost:3000
   - Production build: `npm run build && npm start`

### Docker Development

```bash
# From project root
docker-compose up web
```

## 🎨 Features

### Progressive Web App (PWA)
- **Offline Support**: Essential data cached for offline access
- **Push Notifications**: Real-time transaction updates
- **App-like Experience**: Install on mobile and desktop
- **Service Worker**: Background sync and caching

### Responsive Design
- **Mobile-First**: Optimized for mobile devices
- **Tablet Support**: Adaptive layouts for tablets
- **Desktop Experience**: Full-featured desktop interface
- **Dark/Light Mode**: User preference-based theming

### Real-time Updates
- **WebSocket Integration**: Live transaction status updates
- **Balance Refresh**: Automatic balance synchronization
- **Notification System**: In-app notifications for events

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret

# PWA Configuration
NEXT_PUBLIC_PWA_NAME="Sound Pesa"
NEXT_PUBLIC_PWA_SHORT_NAME="SoundPesa"

# Analytics (optional)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

### Next.js Configuration

```javascript
// next.config.ts
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  images: {
    domains: ['api.soundpesa.com'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
};
```

## 🎯 Key Components

### Authentication Components

```typescript
// components/auth/LoginForm.tsx
import { useState } from 'react';
import { useAuth } from '@/contexts/auth-context';

export function LoginForm() {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const { login, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(credentials);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Form fields */}
    </form>
  );
}
```

### Wallet Dashboard

```typescript
// components/wallet/WalletDashboard.tsx
import { useWallet } from '@/hooks/use-wallet';
import { BalanceCard } from './BalanceCard';
import { TransactionHistory } from './TransactionHistory';

export function WalletDashboard() {
  const { wallets, balances, isLoading } = useWallet();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {wallets.map((wallet) => (
        <BalanceCard
          key={wallet.id}
          wallet={wallet}
          balance={balances[wallet.blockchain]}
        />
      ))}
      <TransactionHistory />
    </div>
  );
}
```

### Transaction Form

```typescript
// components/wallet/SendTransactionForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { sendTransactionSchema } from '@/lib/validations';

export function SendTransactionForm() {
  const form = useForm({
    resolver: zodResolver(sendTransactionSchema),
  });

  const onSubmit = async (data: SendTransactionData) => {
    // Handle transaction submission
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields with validation */}
    </form>
  );
}
```

## 🔐 Security Features

### Authentication & Authorization

```typescript
// contexts/auth-context.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { User } from '@/types/user';
import { api } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    checkAuthStatus();
  }, []);

  // Implementation details...
}
```

### Input Validation

```typescript
// lib/validations.ts
import { z } from 'zod';

export const sendTransactionSchema = z.object({
  blockchain: z.enum(['bitcoin', 'ethereum', 'cardano', 'polkadot']),
  toAddress: z.string().min(1, 'Recipient address is required'),
  amount: z.string().refine((val) => {
    const num = parseFloat(val);
    return !isNaN(num) && num > 0;
  }, 'Amount must be a positive number'),
  fee: z.string().optional(),
});

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});
```

## 🎨 Styling & UI

### Tailwind CSS Configuration

```javascript
// tailwind.config.ts
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
        // Custom color palette
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

### Component Library

```typescript
// components/ui/Button.tsx
import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          {
            'bg-primary-600 text-white hover:bg-primary-700': variant === 'primary',
            'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
            'border border-gray-300 bg-transparent hover:bg-gray-50': variant === 'outline',
          },
          {
            'h-8 px-3 text-sm': size === 'sm',
            'h-10 px-4': size === 'md',
            'h-12 px-6 text-lg': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
```

## 🧪 Testing

### Testing Setup

```bash
# Install testing dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### Component Testing

```typescript
// __tests__/components/Button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('applies correct variant styles', () => {
    render(<Button variant="primary">Primary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-primary-600');
  });
});
```

### Integration Testing

```typescript
// __tests__/pages/dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from '@/app/dashboard/page';
import { AuthProvider } from '@/contexts/auth-context';

const MockedDashboard = () => (
  <AuthProvider>
    <Dashboard />
  </AuthProvider>
);

describe('Dashboard Page', () => {
  it('displays wallet balances', async () => {
    render(<MockedDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/bitcoin balance/i)).toBeInTheDocument();
      expect(screen.getByText(/ethereum balance/i)).toBeInTheDocument();
    });
  });
});
```

## 📱 PWA Configuration

### Manifest File

```json
// public/manifest.json
{
  "name": "Sound Pesa",
  "short_name": "SoundPesa",
  "description": "Multi-chain cryptocurrency wallet",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Service Worker

```javascript
// public/sw.js
const CACHE_NAME = 'sound-pesa-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/static/js/bundle.js',
  '/static/css/main.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});
```

## 🚀 Deployment

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start

# Export static files (if needed)
npm run export
```

### Docker Production

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

### Environment-Specific Configurations

```bash
# Production environment
NEXT_PUBLIC_API_URL=https://api.soundpesa.com
NEXT_PUBLIC_WS_URL=wss://api.soundpesa.com/ws

# Staging environment
NEXT_PUBLIC_API_URL=https://staging-api.soundpesa.com
NEXT_PUBLIC_WS_URL=wss://staging-api.soundpesa.com/ws
```

## 🐛 Troubleshooting

### Common Issues

**Build Errors:**
```bash
# Clear Next.js cache
rm -rf .next

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API Connection Issues:**
```bash
# Check API endpoint
curl https://api.soundpesa.com/api/health/

# Verify environment variables
echo $NEXT_PUBLIC_API_URL
```

**PWA Issues:**
```bash
# Check service worker registration
# Open browser dev tools -> Application -> Service Workers

# Clear PWA cache
# Application -> Storage -> Clear storage
```

## 📊 Performance Optimization

### Code Splitting

```typescript
// Dynamic imports for better performance
import dynamic from 'next/dynamic';

const WalletDashboard = dynamic(() => import('@/components/wallet/WalletDashboard'), {
  loading: () => <LoadingSpinner />,
});
```

### Image Optimization

```typescript
// Using Next.js Image component
import Image from 'next/image';

export function CryptoIcon({ symbol }: { symbol: string }) {
  return (
    <Image
      src={`/icons/${symbol.toLowerCase()}.png`}
      alt={`${symbol} icon`}
      width={32}
      height={32}
      priority
    />
  );
}
```

## 🤝 Contributing

1. Follow the established component patterns
2. Use TypeScript for all new code
3. Write tests for new components and features
4. Follow the existing styling conventions
5. Update documentation for new features