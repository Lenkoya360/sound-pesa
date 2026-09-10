/**
 * Bitcoin-specific utilities and constants
 */

export const BITCOIN_NETWORKS = {
  MAINNET: 'mainnet',
  TESTNET: 'testnet',
  REGTEST: 'regtest'
} as const;

export const BITCOIN_ADDRESS_TYPES = {
  P2PKH: 'p2pkh', // Legacy addresses starting with 1
  P2SH: 'p2sh',   // Script addresses starting with 3
  BECH32: 'bech32' // Native SegWit addresses starting with bc1
} as const;

/**
 * Bitcoin network configuration
 */
export interface BitcoinNetworkConfig {
  name: string;
  rpc_port: number;
  p2p_port: number;
  address_prefix: string;
  wif_prefix: number;
  bech32_hrp: string;
}

export const BITCOIN_NETWORK_CONFIGS: Record<string, BitcoinNetworkConfig> = {
  mainnet: {
    name: 'mainnet',
    rpc_port: 8332,
    p2p_port: 8333,
    address_prefix: '1',
    wif_prefix: 0x80,
    bech32_hrp: 'bc'
  },
  testnet: {
    name: 'testnet',
    rpc_port: 18332,
    p2p_port: 18333,
    address_prefix: 'm',
    wif_prefix: 0xef,
    bech32_hrp: 'tb'
  }
};

/**
 * Convert satoshis to BTC
 */
export function satoshisToBTC(satoshis: number): string {
  return (satoshis / 100000000).toFixed(8);
}

/**
 * Convert BTC to satoshis
 */
export function btcToSatoshis(btc: string): number {
  return Math.floor(parseFloat(btc) * 100000000);
}

/**
 * Validate Bitcoin address format
 */
export function isValidBitcoinAddress(address: string, network: string = 'mainnet'): boolean {
  const config = BITCOIN_NETWORK_CONFIGS[network];
  if (!config) return false;
  
  // Legacy P2PKH addresses
  if (address.startsWith(config.address_prefix)) {
    return /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(address);
  }
  
  // Bech32 addresses
  if (address.startsWith(config.bech32_hrp)) {
    return new RegExp(`^${config.bech32_hrp}1[a-z0-9]{39,59}$`).test(address);
  }
  
  return false;
}

/**
 * Estimate Bitcoin transaction fee based on size and fee rate
 */
export function estimateBitcoinFee(inputCount: number, outputCount: number, feeRatePerByte: number): number {
  // Simplified fee calculation
  // Actual implementation would be more complex
  const baseSize = 10; // Base transaction size
  const inputSize = 148; // Average input size
  const outputSize = 34; // Average output size
  
  const totalSize = baseSize + (inputCount * inputSize) + (outputCount * outputSize);
  return totalSize * feeRatePerByte;
}