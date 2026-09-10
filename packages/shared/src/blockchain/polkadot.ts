/**
 * Polkadot-specific utilities and constants
 */

export const POLKADOT_NETWORKS = {
  POLKADOT: 'polkadot',
  KUSAMA: 'kusama',
  WESTEND: 'westend'
} as const;

/**
 * Polkadot network configuration
 */
export interface PolkadotNetworkConfig {
  name: string;
  ss58_prefix: number;
  decimals: number;
  symbol: string;
  explorer_url: string;
}

export const POLKADOT_NETWORK_CONFIGS: Record<string, PolkadotNetworkConfig> = {
  polkadot: {
    name: 'Polkadot',
    ss58_prefix: 0,
    decimals: 10,
    symbol: 'DOT',
    explorer_url: 'https://polkadot.subscan.io'
  },
  kusama: {
    name: 'Kusama',
    ss58_prefix: 2,
    decimals: 12,
    symbol: 'KSM',
    explorer_url: 'https://kusama.subscan.io'
  },
  westend: {
    name: 'Westend',
    ss58_prefix: 42,
    decimals: 12,
    symbol: 'WND',
    explorer_url: 'https://westend.subscan.io'
  }
};

/**
 * Convert planck to DOT
 */
export function planckToDot(planck: string): string {
  const planckNum = parseFloat(planck);
  const dotNum = planckNum / Math.pow(10, 10);
  return dotNum.toFixed(10);
}

/**
 * Convert DOT to planck
 */
export function dotToPlanck(dot: string): string {
  const dotNum = parseFloat(dot);
  const planckNum = Math.floor(dotNum * Math.pow(10, 10));
  return planckNum.toString();
}

/**
 * Validate Polkadot address format (SS58)
 */
export function isValidPolkadotAddress(address: string, network: string = 'polkadot'): boolean {
  const config = POLKADOT_NETWORK_CONFIGS[network];
  if (!config) return false;
  
  // Basic SS58 address validation
  // In production, use proper SS58 decoding library
  return /^1[a-zA-Z0-9]{47}$/.test(address) || /^5[a-zA-Z0-9]{47}$/.test(address);
}

/**
 * Calculate Polkadot transaction fee (simplified)
 */
export function calculatePolkadotFee(weight: number, feeMultiplier: number = 1): string {
  // Simplified fee calculation
  // Actual Polkadot fee calculation uses weight and fee multiplier
  const baseFee = 125000000; // Base fee in planck
  const weightFee = weight * feeMultiplier;
  const totalFee = baseFee + weightFee;
  
  return totalFee.toString();
}

/**
 * Estimate transaction weight for different operations
 */
export function estimateTransactionWeight(operation: 'transfer' | 'stake' | 'unstake'): number {
  switch (operation) {
    case 'transfer':
      return 195000000; // Weight for balance transfer
    case 'stake':
      return 210000000; // Weight for staking
    case 'unstake':
      return 190000000; // Weight for unstaking
    default:
      return 195000000;
  }
}

/**
 * Polkadot existential deposit (minimum balance)
 */
export const EXISTENTIAL_DEPOSIT = '1.0000000000'; // 1 DOT

/**
 * Common Polkadot parachains
 */
export const POLKADOT_PARACHAINS = {
  ACALA: 'acala',
  MOONBEAM: 'moonbeam',
  ASTAR: 'astar',
  PARALLEL: 'parallel'
} as const;