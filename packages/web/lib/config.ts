import { z } from 'zod'

// Environment validation schema
const envSchema = z.object({
  // API Configuration
  NEXT_PUBLIC_API_URL: z.string().url().default('http://localhost:8000/api'),
  NEXT_PUBLIC_WS_URL: z.string().default('ws://localhost:8000/ws'),
  
  // Environment
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  NEXT_PUBLIC_APP_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  
  // Application Configuration
  NEXT_PUBLIC_APP_NAME: z.string().default('Sound Pesa'),
  NEXT_PUBLIC_APP_DESCRIPTION: z.string().default('Multi-chain cryptocurrency platform'),
  NEXT_PUBLIC_APP_VERSION: z.string().default('1.0.0'),
  
  // Feature Flags
  NEXT_PUBLIC_ENABLE_2FA: z.string().transform(val => val === 'true').default('true'),
  NEXT_PUBLIC_ENABLE_BIOMETRIC_AUTH: z.string().transform(val => val === 'true').default('true'),
  NEXT_PUBLIC_ENABLE_PWA: z.string().transform(val => val === 'true').default('true'),
  
  // Blockchain Configuration
  NEXT_PUBLIC_BITCOIN_NETWORK: z.enum(['mainnet', 'testnet', 'regtest']).default('testnet'),
  NEXT_PUBLIC_ETHEREUM_NETWORK: z.enum(['mainnet', 'sepolia', 'goerli', 'localhost']).default('sepolia'),
  NEXT_PUBLIC_CARDANO_NETWORK: z.enum(['mainnet', 'testnet', 'preview']).default('testnet'),
  NEXT_PUBLIC_POLKADOT_NETWORK: z.enum(['polkadot', 'kusama', 'westend', 'rococo']).default('westend'),
  
  // Security
  NEXT_PUBLIC_JWT_REFRESH_THRESHOLD: z.string().transform(val => parseInt(val, 10)).default('300000'),
  NEXT_PUBLIC_SESSION_TIMEOUT: z.string().transform(val => parseInt(val, 10)).default('3600000'),
  
  // Analytics (optional)
  NEXT_PUBLIC_ANALYTICS_ID: z.string().optional(),
  NEXT_PUBLIC_SENTRY_DSN: z.string().optional(),
  
  // Development
  NEXT_PUBLIC_DEBUG: z.string().transform(val => val === 'true').default('false'),
  NEXT_PUBLIC_MOCK_API: z.string().transform(val => val === 'true').default('false'),
})

// Parse and validate environment variables
const parseEnv = () => {
  try {
    return envSchema.parse(process.env)
  } catch (error) {
    console.error('❌ Invalid environment variables:', error)
    throw new Error('Invalid environment configuration')
  }
}

// Export validated configuration
export const config = parseEnv()

// Type-safe environment configuration
export type Config = z.infer<typeof envSchema>

// Helper functions
export const isDevelopment = config.NODE_ENV === 'development'
export const isProduction = config.NODE_ENV === 'production'
export const isTest = config.NODE_ENV === 'test'

// API endpoints
export const apiEndpoints = {
  auth: {
    login: `${config.NEXT_PUBLIC_API_URL}/auth/login`,
    register: `${config.NEXT_PUBLIC_API_URL}/auth/register`,
    logout: `${config.NEXT_PUBLIC_API_URL}/auth/logout`,
    refresh: `${config.NEXT_PUBLIC_API_URL}/auth/refresh`,
    profile: `${config.NEXT_PUBLIC_API_URL}/user/profile`,
  },
  wallets: {
    list: `${config.NEXT_PUBLIC_API_URL}/wallets`,
    create: `${config.NEXT_PUBLIC_API_URL}/wallets/create`,
    balance: (chain: string) => `${config.NEXT_PUBLIC_API_URL}/wallets/${chain}/balance`,
    history: (chain: string) => `${config.NEXT_PUBLIC_API_URL}/wallets/${chain}/history`,
  },
  transactions: {
    send: `${config.NEXT_PUBLIC_API_URL}/transactions/send`,
    get: (id: string) => `${config.NEXT_PUBLIC_API_URL}/transactions/${id}`,
    pending: `${config.NEXT_PUBLIC_API_URL}/transactions/pending`,
    estimateFee: `${config.NEXT_PUBLIC_API_URL}/transactions/estimate-fee`,
  },
  blockchain: {
    status: (chain: string) => `${config.NEXT_PUBLIC_API_URL}/blockchain/${chain}/status`,
    blockHeight: (chain: string) => `${config.NEXT_PUBLIC_API_URL}/blockchain/${chain}/block-height`,
  },
} as const

// WebSocket endpoints
export const wsEndpoints = {
  transactions: `${config.NEXT_PUBLIC_WS_URL}/transactions`,
  balances: `${config.NEXT_PUBLIC_WS_URL}/balances`,
  blockchain: `${config.NEXT_PUBLIC_WS_URL}/blockchain`,
} as const

// Blockchain network configurations
export const blockchainNetworks = {
  bitcoin: config.NEXT_PUBLIC_BITCOIN_NETWORK,
  ethereum: config.NEXT_PUBLIC_ETHEREUM_NETWORK,
  cardano: config.NEXT_PUBLIC_CARDANO_NETWORK,
  polkadot: config.NEXT_PUBLIC_POLKADOT_NETWORK,
} as const