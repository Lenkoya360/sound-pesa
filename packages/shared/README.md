# Sound Pesa Shared Package

Shared utilities, types, and constants used across all Sound Pesa platform services including API, web application, and mobile app.

## 🏗️ Package Structure

```
packages/shared/
├── src/
│   ├── types/              # TypeScript type definitions
│   │   ├── api.ts         # API request/response types
│   │   ├── blockchain.ts  # Blockchain-specific types
│   │   ├── transaction.ts # Transaction data structures
│   │   └── user.ts        # User and authentication types
│   ├── utils/             # Utility functions
│   │   ├── constants.ts   # Platform-wide constants
│   │   ├── crypto.ts      # Cryptographic utilities
│   │   ├── formatting.ts  # Data formatting helpers
│   │   └── validation.ts  # Input validation schemas
│   ├── blockchain/        # Blockchain-specific utilities
│   │   ├── bitcoin.ts     # Bitcoin utilities
│   │   ├── cardano.ts     # Cardano utilities
│   │   ├── ethereum.ts    # Ethereum utilities
│   │   └── polkadot.ts    # Polkadot utilities
│   ├── config/            # Configuration management
│   │   ├── environment.ts # Environment-specific settings
│   │   └── networks.ts    # Blockchain network configurations
│   └── index.ts           # Main export file
├── dist/                  # Compiled JavaScript output
├── package.json
├── tsconfig.json
└── README.md
```

## 🚀 Installation & Usage

### Installation

```bash
# Install in API package
cd packages/api
npm install ../shared

# Install in web package
cd packages/web
npm install ../shared

# Install in mobile app
cd packages/app
npm install ../shared
```

### Usage Examples

```typescript
// Import types
import { User, Wallet, Transaction } from '@sound-pesa/shared/types';

// Import utilities
import { validateAddress, formatCurrency } from '@sound-pesa/shared/utils';

// Import blockchain utilities
import { BitcoinUtils, EthereumUtils } from '@sound-pesa/shared/blockchain';

// Import constants
import { SUPPORTED_BLOCKCHAINS, API_ENDPOINTS } from '@sound-pesa/shared/constants';
```

## 📝 Type Definitions

### User Types

```typescript
// types/user.ts
export interface User {
  id: string;
  email: string;
  username: string;
  created_at: Date;
  updated_at: Date;
  is_active: boolean;
  two_factor_enabled: boolean;
  kyc_status: KYCStatus;
}

export interface UserProfile {
  user_id: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  country: string;
  date_of_birth?: Date;
}

export type KYCStatus = 'pending' | 'approved' | 'rejected' | 'not_started';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'Bearer';
}

export interface LoginCredentials {
  email: string;
  password: string;
  two_factor_code?: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
  country: string;
}
```

### Blockchain Types

```typescript
// types/blockchain.ts
export type BlockchainNetwork = 'bitcoin' | 'ethereum' | 'cardano' | 'polkadot';

export interface Wallet {
  id: string;
  user_id: string;
  blockchain: BlockchainNetwork;
  address: string;
  encrypted_private_key: string;
  created_at: Date;
  is_active: boolean;
  label?: string;
}

export interface WalletBalance {
  wallet_id: string;
  blockchain: BlockchainNetwork;
  balance: string;
  confirmed_balance: string;
  unconfirmed_balance: string;
  last_updated: Date;
  currency_symbol: string;
}

export interface BlockchainStatus {
  blockchain: BlockchainNetwork;
  is_synced: boolean;
  current_block: number;
  highest_block: number;
  sync_percentage: number;
  peer_count: number;
  last_block_time: Date;
  network: 'mainnet' | 'testnet';
}

export interface NetworkFee {
  blockchain: BlockchainNetwork;
  slow: string;
  standard: string;
  fast: string;
  unit: string;
}
```

### Transaction Types

```typescript
// types/transaction.ts
export interface Transaction {
  id: string;
  user_id: string;
  from_wallet_id: string;
  to_address: string;
  blockchain: BlockchainNetwork;
  amount: string;
  fee: string;
  status: TransactionStatus;
  transaction_hash?: string;
  block_height?: number;
  confirmations: number;
  created_at: Date;
  confirmed_at?: Date;
  notes?: string;
}

export type TransactionStatus = 
  | 'pending' 
  | 'confirmed' 
  | 'failed' 
  | 'cancelled' 
  | 'expired';

export interface TransactionEstimate {
  blockchain: BlockchainNetwork;
  amount: string;
  estimated_fee: string;
  estimated_confirmation_time: number; // minutes
  network_congestion: 'low' | 'medium' | 'high';
}

export interface SendTransactionRequest {
  blockchain: BlockchainNetwork;
  to_address: string;
  amount: string;
  fee_level: 'slow' | 'standard' | 'fast';
  notes?: string;
}

export interface TransactionHistory {
  transactions: Transaction[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}
```

### API Types

```typescript
// types/api.ts
export interface APIResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
  timestamp: Date;
}

export interface APIError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    timestamp: Date;
    request_id: string;
  };
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
  page_size: number;
  current_page: number;
  total_pages: number;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  version: string;
  timestamp: Date;
  services: {
    database: 'up' | 'down';
    redis: 'up' | 'down';
    blockchain_nodes: Record<BlockchainNetwork, 'up' | 'down'>;
  };
}
```

## 🛠️ Utility Functions

### Validation Utilities

```typescript
// utils/validation.ts
import { z } from 'zod';

export const emailSchema = z.string().email('Invalid email address');

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character');

export const addressValidationSchemas = {
  bitcoin: z.string().regex(/^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$/),
  ethereum: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
  cardano: z.string().regex(/^addr1[a-z0-9]{98}$/),
  polkadot: z.string().regex(/^[1-9A-HJ-NP-Za-km-z]{47,48}$/),
};

export function validateAddress(address: string, blockchain: BlockchainNetwork): boolean {
  const schema = addressValidationSchemas[blockchain];
  return schema.safeParse(address).success;
}

export function validateAmount(amount: string): boolean {
  const num = parseFloat(amount);
  return !isNaN(num) && num > 0 && /^\d+(\.\d{1,8})?$/.test(amount);
}

export const transactionSchema = z.object({
  blockchain: z.enum(['bitcoin', 'ethereum', 'cardano', 'polkadot']),
  to_address: z.string().min(1, 'Recipient address is required'),
  amount: z.string().refine(validateAmount, 'Invalid amount format'),
  fee_level: z.enum(['slow', 'standard', 'fast']),
  notes: z.string().max(500).optional(),
});
```

### Formatting Utilities

```typescript
// utils/formatting.ts
export function formatCurrency(
  amount: string | number,
  currency: string,
  decimals: number = 8
): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (isNaN(num)) return '0';
  
  return `${num.toFixed(decimals)} ${currency.toUpperCase()}`;
}

export function formatAddress(address: string, length: number = 8): string {
  if (address.length <= length * 2) return address;
  
  return `${address.slice(0, length)}...${address.slice(-length)}`;
}

export function formatTransactionHash(hash: string): string {
  return formatAddress(hash, 6);
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return formatDate(d);
}

export function formatFileSize(bytes: number): string {
  const sizes = ['B', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 B';
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}
```

### Cryptographic Utilities

```typescript
// utils/crypto.ts
import CryptoJS from 'crypto-js';

export function generateSecureRandom(length: number = 32): string {
  return CryptoJS.lib.WordArray.random(length).toString();
}

export function hashPassword(password: string, salt?: string): string {
  const saltToUse = salt || generateSecureRandom(16);
  return CryptoJS.PBKDF2(password, saltToUse, {
    keySize: 256 / 32,
    iterations: 10000,
  }).toString();
}

export function encryptData(data: string, key: string): string {
  return CryptoJS.AES.encrypt(data, key).toString();
}

export function decryptData(encryptedData: string, key: string): string {
  const bytes = CryptoJS.AES.decrypt(encryptedData, key);
  return bytes.toString(CryptoJS.enc.Utf8);
}

export function generateMnemonic(): string[] {
  // Implementation would use a proper BIP39 library
  // This is a placeholder for the actual implementation
  const words = [
    'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb',
    // ... full BIP39 wordlist
  ];
  
  const mnemonic: string[] = [];
  for (let i = 0; i < 12; i++) {
    const randomIndex = Math.floor(Math.random() * words.length);
    mnemonic.push(words[randomIndex]);
  }
  
  return mnemonic;
}

export function validateMnemonic(mnemonic: string[]): boolean {
  // Implementation would validate against BIP39 standard
  return mnemonic.length === 12 || mnemonic.length === 24;
}
```

## ⛓️ Blockchain Utilities

### Bitcoin Utilities

```typescript
// blockchain/bitcoin.ts
export class BitcoinUtils {
  static readonly NETWORK_CONFIGS = {
    mainnet: {
      name: 'Bitcoin Mainnet',
      symbol: 'BTC',
      decimals: 8,
      confirmations: 6,
      addressPrefix: ['1', '3', 'bc1'],
    },
    testnet: {
      name: 'Bitcoin Testnet',
      symbol: 'tBTC',
      decimals: 8,
      confirmations: 3,
      addressPrefix: ['m', 'n', '2', 'tb1'],
    },
  };

  static validateAddress(address: string, network: 'mainnet' | 'testnet' = 'mainnet'): boolean {
    const config = this.NETWORK_CONFIGS[network];
    return config.addressPrefix.some(prefix => address.startsWith(prefix));
  }

  static satoshisToBTC(satoshis: number): string {
    return (satoshis / 100000000).toFixed(8);
  }

  static btcToSatoshis(btc: string | number): number {
    const amount = typeof btc === 'string' ? parseFloat(btc) : btc;
    return Math.round(amount * 100000000);
  }

  static estimateFee(inputCount: number, outputCount: number, feeRate: number): number {
    // Simplified fee estimation (actual implementation would be more complex)
    const txSize = inputCount * 148 + outputCount * 34 + 10;
    return txSize * feeRate;
  }

  static formatTransactionUrl(txHash: string, network: 'mainnet' | 'testnet' = 'mainnet'): string {
    const baseUrl = network === 'mainnet' 
      ? 'https://blockstream.info/tx/' 
      : 'https://blockstream.info/testnet/tx/';
    return `${baseUrl}${txHash}`;
  }
}
```

### Ethereum Utilities

```typescript
// blockchain/ethereum.ts
export class EthereumUtils {
  static readonly NETWORK_CONFIGS = {
    mainnet: {
      name: 'Ethereum Mainnet',
      symbol: 'ETH',
      decimals: 18,
      confirmations: 12,
      chainId: 1,
    },
    goerli: {
      name: 'Goerli Testnet',
      symbol: 'ETH',
      decimals: 18,
      confirmations: 6,
      chainId: 5,
    },
  };

  static validateAddress(address: string): boolean {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
  }

  static weiToEth(wei: string | number): string {
    const amount = typeof wei === 'string' ? BigInt(wei) : BigInt(wei);
    return (Number(amount) / 1e18).toFixed(18);
  }

  static ethToWei(eth: string | number): string {
    const amount = typeof eth === 'string' ? parseFloat(eth) : eth;
    return (BigInt(Math.round(amount * 1e18))).toString();
  }

  static estimateGas(to: string, value: string, data?: string): number {
    // Simplified gas estimation
    let gasLimit = 21000; // Base transaction cost
    
    if (data && data !== '0x') {
      gasLimit += data.length * 68; // Data cost
    }
    
    return gasLimit;
  }

  static formatTransactionUrl(txHash: string, network: 'mainnet' | 'goerli' = 'mainnet'): string {
    const baseUrl = network === 'mainnet' 
      ? 'https://etherscan.io/tx/' 
      : 'https://goerli.etherscan.io/tx/';
    return `${baseUrl}${txHash}`;
  }
}
```

## ⚙️ Configuration

### Network Configurations

```typescript
// config/networks.ts
export const BLOCKCHAIN_NETWORKS = {
  bitcoin: {
    mainnet: {
      name: 'Bitcoin',
      symbol: 'BTC',
      decimals: 8,
      confirmations: 6,
      rpcPort: 8332,
      explorerUrl: 'https://blockstream.info',
    },
    testnet: {
      name: 'Bitcoin Testnet',
      symbol: 'tBTC',
      decimals: 8,
      confirmations: 3,
      rpcPort: 18332,
      explorerUrl: 'https://blockstream.info/testnet',
    },
  },
  ethereum: {
    mainnet: {
      name: 'Ethereum',
      symbol: 'ETH',
      decimals: 18,
      confirmations: 12,
      rpcPort: 8545,
      chainId: 1,
      explorerUrl: 'https://etherscan.io',
    },
    goerli: {
      name: 'Goerli',
      symbol: 'ETH',
      decimals: 18,
      confirmations: 6,
      rpcPort: 8545,
      chainId: 5,
      explorerUrl: 'https://goerli.etherscan.io',
    },
  },
  // ... other networks
} as const;

export type NetworkConfig = typeof BLOCKCHAIN_NETWORKS;
export type SupportedNetwork = keyof NetworkConfig;
```

### Constants

```typescript
// utils/constants.ts
export const SUPPORTED_BLOCKCHAINS = ['bitcoin', 'ethereum', 'cardano', 'polkadot'] as const;

export const CURRENCY_SYMBOLS = {
  bitcoin: 'BTC',
  ethereum: 'ETH',
  cardano: 'ADA',
  polkadot: 'DOT',
} as const;

export const TRANSACTION_STATUSES = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
} as const;

export const API_ENDPOINTS = {
  AUTH: '/api/auth',
  WALLETS: '/api/wallets',
  TRANSACTIONS: '/api/transactions',
  BLOCKCHAIN: '/api/blockchain',
  USER: '/api/user',
} as const;

export const ERROR_CODES = {
  // Authentication errors
  AUTH_INVALID_CREDENTIALS: 'AUTH_INVALID_CREDENTIALS',
  AUTH_TOKEN_EXPIRED: 'AUTH_TOKEN_EXPIRED',
  AUTH_2FA_REQUIRED: 'AUTH_2FA_REQUIRED',
  
  // Validation errors
  VALIDATION_INVALID_ADDRESS: 'VALIDATION_INVALID_ADDRESS',
  VALIDATION_INSUFFICIENT_BALANCE: 'VALIDATION_INSUFFICIENT_BALANCE',
  VALIDATION_AMOUNT_TOO_SMALL: 'VALIDATION_AMOUNT_TOO_SMALL',
  
  // Blockchain errors
  BLOCKCHAIN_NODE_UNAVAILABLE: 'BLOCKCHAIN_NODE_UNAVAILABLE',
  BLOCKCHAIN_TRANSACTION_FAILED: 'BLOCKCHAIN_TRANSACTION_FAILED',
  BLOCKCHAIN_NETWORK_CONGESTION: 'BLOCKCHAIN_NETWORK_CONGESTION',
} as const;

export const PAGINATION_DEFAULTS = {
  PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Examples

```typescript
// __tests__/utils/validation.test.ts
import { validateAddress, validateAmount } from '../src/utils/validation';

describe('Validation Utils', () => {
  describe('validateAddress', () => {
    it('validates Bitcoin addresses correctly', () => {
      expect(validateAddress('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', 'bitcoin')).toBe(true);
      expect(validateAddress('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4', 'bitcoin')).toBe(true);
      expect(validateAddress('invalid-address', 'bitcoin')).toBe(false);
    });

    it('validates Ethereum addresses correctly', () => {
      expect(validateAddress('0x742d35Cc6634C0532925a3b8D400E4C0C0C8C0C8', 'ethereum')).toBe(true);
      expect(validateAddress('0xinvalid', 'ethereum')).toBe(false);
    });
  });

  describe('validateAmount', () => {
    it('validates positive amounts', () => {
      expect(validateAmount('1.5')).toBe(true);
      expect(validateAmount('0.00000001')).toBe(true);
      expect(validateAmount('1000')).toBe(true);
    });

    it('rejects invalid amounts', () => {
      expect(validateAmount('0')).toBe(false);
      expect(validateAmount('-1')).toBe(false);
      expect(validateAmount('abc')).toBe(false);
    });
  });
});
```

## 🚀 Building & Publishing

### Build Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Package Configuration

```json
// package.json
{
  "name": "@sound-pesa/shared",
  "version": "1.0.0",
  "description": "Shared utilities and types for Sound Pesa platform",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "build:watch": "tsc --watch",
    "test": "jest",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix"
  },
  "dependencies": {
    "crypto-js": "^4.1.1",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/crypto-js": "^4.1.1",
    "@types/jest": "^29.5.5",
    "jest": "^29.7.0",
    "typescript": "^5.2.2"
  }
}
```

### Building the Package

```bash
# Build TypeScript to JavaScript
npm run build

# Build and watch for changes
npm run build:watch

# Run linting
npm run lint
```

## 🤝 Contributing

1. Follow TypeScript best practices
2. Write comprehensive tests for new utilities
3. Update type definitions for new features
4. Maintain backward compatibility
5. Document all public APIs
6. Use semantic versioning for releases