/**
 * Ethereum-specific utilities and constants
 */

export const ETHEREUM_NETWORKS = {
  MAINNET: 'mainnet',
  GOERLI: 'goerli',
  SEPOLIA: 'sepolia'
} as const;

export const ETHEREUM_CHAIN_IDS = {
  MAINNET: 1,
  GOERLI: 5,
  SEPOLIA: 11155111
} as const;

/**
 * Ethereum network configuration
 */
export interface EthereumNetworkConfig {
  name: string;
  chain_id: number;
  rpc_url: string;
  explorer_url: string;
  currency_symbol: string;
}

export const ETHEREUM_NETWORK_CONFIGS: Record<string, EthereumNetworkConfig> = {
  mainnet: {
    name: 'Ethereum Mainnet',
    chain_id: 1,
    rpc_url: 'https://mainnet.infura.io/v3/',
    explorer_url: 'https://etherscan.io',
    currency_symbol: 'ETH'
  },
  goerli: {
    name: 'Goerli Testnet',
    chain_id: 5,
    rpc_url: 'https://goerli.infura.io/v3/',
    explorer_url: 'https://goerli.etherscan.io',
    currency_symbol: 'GoerliETH'
  }
};

/**
 * Convert wei to ether
 */
export function weiToEther(wei: string): string {
  const weiNum = BigInt(wei);
  const etherNum = Number(weiNum) / Math.pow(10, 18);
  return etherNum.toString();
}

/**
 * Convert ether to wei
 */
export function etherToWei(ether: string): string {
  const etherNum = parseFloat(ether);
  const weiNum = BigInt(Math.floor(etherNum * Math.pow(10, 18)));
  return weiNum.toString();
}

/**
 * Convert gwei to wei
 */
export function gweiToWei(gwei: string): string {
  const gweiNum = parseFloat(gwei);
  const weiNum = BigInt(Math.floor(gweiNum * Math.pow(10, 9)));
  return weiNum.toString();
}

/**
 * Convert wei to gwei
 */
export function weiToGwei(wei: string): string {
  const weiNum = BigInt(wei);
  const gweiNum = Number(weiNum) / Math.pow(10, 9);
  return gweiNum.toString();
}

/**
 * Validate Ethereum address format
 */
export function isValidEthereumAddress(address: string): boolean {
  return /^0x[a-fA-F0-9]{40}$/.test(address);
}

/**
 * Estimate Ethereum gas limit for different transaction types
 */
export function estimateGasLimit(transactionType: 'transfer' | 'contract' | 'token'): number {
  switch (transactionType) {
    case 'transfer':
      return 21000; // Standard ETH transfer
    case 'token':
      return 65000; // ERC-20 token transfer
    case 'contract':
      return 100000; // Contract interaction (estimate)
    default:
      return 21000;
  }
}

/**
 * Calculate transaction fee in ETH
 */
export function calculateEthereumFee(gasLimit: number, gasPrice: string): string {
  const gasPriceWei = gweiToWei(gasPrice);
  const feeWei = BigInt(gasLimit) * BigInt(gasPriceWei);
  return weiToEther(feeWei.toString());
}

/**
 * Common ERC-20 token addresses on mainnet
 */
export const COMMON_ERC20_TOKENS = {
  USDC: '0xA0b86a33E6441b8C4505E2c8C5B8c8C5C5C5C5C5',
  USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
  DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F'
} as const;