/**
 * Cardano-specific utilities and constants
 */

export const CARDANO_NETWORKS = {
  MAINNET: 'mainnet',
  TESTNET: 'testnet',
  PREVIEW: 'preview',
  PREPROD: 'preprod'
} as const;

/**
 * Cardano network configuration
 */
export interface CardanoNetworkConfig {
  name: string;
  network_id: number;
  protocol_magic: number;
  explorer_url: string;
  currency_symbol: string;
}

export const CARDANO_NETWORK_CONFIGS: Record<string, CardanoNetworkConfig> = {
  mainnet: {
    name: 'Cardano Mainnet',
    network_id: 1,
    protocol_magic: 764824073,
    explorer_url: 'https://cardanoscan.io',
    currency_symbol: 'ADA'
  },
  testnet: {
    name: 'Cardano Testnet',
    network_id: 0,
    protocol_magic: 1097911063,
    explorer_url: 'https://testnet.cardanoscan.io',
    currency_symbol: 'tADA'
  }
};

/**
 * Convert lovelace to ADA
 */
export function lovelaceToAda(lovelace: string): string {
  const lovelaceNum = parseFloat(lovelace);
  const adaNum = lovelaceNum / 1000000;
  return adaNum.toFixed(6);
}

/**
 * Convert ADA to lovelace
 */
export function adaToLovelace(ada: string): string {
  const adaNum = parseFloat(ada);
  const lovelaceNum = Math.floor(adaNum * 1000000);
  return lovelaceNum.toString();
}

/**
 * Validate Cardano address format
 */
export function isValidCardanoAddress(address: string): boolean {
  // Shelley era addresses (addr1...)
  if (address.startsWith('addr1')) {
    return /^addr1[a-z0-9]{58}$/.test(address);
  }
  
  // Byron era addresses (DdzFF...)
  if (address.startsWith('DdzFF')) {
    return /^DdzFF[a-zA-Z0-9]{93}$/.test(address);
  }
  
  return false;
}

/**
 * Cardano transaction fee calculation (simplified)
 */
export function calculateCardanoFee(txSize: number, feePerByte: number = 44): number {
  // Simplified fee calculation
  // Actual Cardano fee calculation is more complex
  const baseFee = 155381; // Base fee in lovelace
  const sizeFee = txSize * feePerByte;
  return baseFee + sizeFee;
}

/**
 * Estimate Cardano transaction size
 */
export function estimateCardanoTxSize(inputCount: number, outputCount: number): number {
  // Simplified size estimation
  const baseSize = 10;
  const inputSize = 180; // Average input size
  const outputSize = 40; // Average output size
  
  return baseSize + (inputCount * inputSize) + (outputCount * outputSize);
}

/**
 * Cardano address types
 */
export const CARDANO_ADDRESS_TYPES = {
  BYRON: 'byron',
  SHELLEY: 'shelley',
  STAKE: 'stake'
} as const;

/**
 * Minimum ADA required for UTxO
 */
export const MIN_UTXO_ADA = '1.000000'; // 1 ADA minimum