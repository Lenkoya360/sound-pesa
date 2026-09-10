import { BlockchainNetwork } from '../types/blockchain';

// Blockchain constants
export const SUPPORTED_BLOCKCHAINS: BlockchainNetwork[] = [
  'bitcoin',
  'ethereum', 
  'cardano',
  'polkadot'
];

export const BLOCKCHAIN_NAMES: Record<BlockchainNetwork, string> = {
  bitcoin: 'Bitcoin',
  ethereum: 'Ethereum',
  cardano: 'Cardano',
  polkadot: 'Polkadot'
};

export const BLOCKCHAIN_SYMBOLS: Record<BlockchainNetwork, string> = {
  bitcoin: 'BTC',
  ethereum: 'ETH',
  cardano: 'ADA',
  polkadot: 'DOT'
};

export const BLOCKCHAIN_DECIMALS: Record<BlockchainNetwork, number> = {
  bitcoin: 8,
  ethereum: 18,
  cardano: 6,
  polkadot: 10
};

// Transaction constants
export const TRANSACTION_STATUSES = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
} as const;

export const FEE_PRIORITIES = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high'
} as const;

export const NETWORK_CONGESTION_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high'
} as const;

// Minimum transaction amounts (in base units)
export const MIN_TRANSACTION_AMOUNTS: Record<BlockchainNetwork, string> = {
  bitcoin: '0.00000546', // 546 satoshis (dust limit)
  ethereum: '0.000000000000000001', // 1 wei
  cardano: '1.000000', // 1 ADA minimum
  polkadot: '0.0000000001' // 1 planck
};

// Maximum transaction amounts (reasonable limits)
export const MAX_TRANSACTION_AMOUNTS: Record<BlockchainNetwork, string> = {
  bitcoin: '21000000', // Total Bitcoin supply
  ethereum: '1000000000', // 1 billion ETH
  cardano: '45000000000', // Total ADA supply
  polkadot: '1000000000' // 1 billion DOT
};

// Confirmation requirements
export const CONFIRMATION_REQUIREMENTS: Record<BlockchainNetwork, number> = {
  bitcoin: 6, // 6 confirmations for Bitcoin
  ethereum: 12, // 12 confirmations for Ethereum
  cardano: 15, // 15 confirmations for Cardano
  polkadot: 6 // 6 confirmations for Polkadot
};

// API constants
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REGISTER: '/api/auth/register',
    REFRESH: '/api/auth/refresh'
  },
  USER: {
    PROFILE: '/api/user/profile'
  },
  WALLETS: {
    LIST: '/api/wallets',
    CREATE: '/api/wallets/create',
    BALANCE: '/api/wallets/{chain}/balance',
    HISTORY: '/api/wallets/{chain}/history'
  },
  TRANSACTIONS: {
    SEND: '/api/transactions/send',
    DETAIL: '/api/transactions/{id}',
    PENDING: '/api/transactions/pending',
    ESTIMATE_FEE: '/api/transactions/estimate-fee'
  },
  BLOCKCHAIN: {
    STATUS: '/api/blockchain/{chain}/status',
    BLOCK_HEIGHT: '/api/blockchain/{chain}/block-height'
  }
} as const;

// Pagination defaults
export const PAGINATION_DEFAULTS = {
  PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100
} as const;

// Cache TTL values (in seconds)
export const CACHE_TTL = {
  BALANCE: 30, // 30 seconds
  TRANSACTION_HISTORY: 60, // 1 minute
  BLOCKCHAIN_STATUS: 10, // 10 seconds
  USER_PROFILE: 300 // 5 minutes
} as const;

// WebSocket event types
export const WS_EVENTS = {
  TRANSACTION_UPDATE: 'transaction_update',
  BALANCE_UPDATE: 'balance_update',
  BLOCKCHAIN_STATUS_UPDATE: 'blockchain_status_update'
} as const;