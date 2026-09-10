import { BlockchainConfig } from '../types/blockchain';

/**
 * Blockchain network configurations for all supported chains
 */
export const NETWORK_CONFIGS: Record<string, BlockchainConfig> = {
  bitcoin: {
    name: 'bitcoin',
    rpc_url: process.env['BITCOIN_RPC_URL'] || 'http://bitcoin-core:8332',
    confirmations_required: 6,
    min_transaction_amount: '0.00000546',
    max_transaction_amount: '21000000',
    address_prefix: '1'
  },
  ethereum: {
    name: 'ethereum',
    rpc_url: process.env['ETHEREUM_RPC_URL'] || 'http://geth:8545',
    network_id: 1,
    confirmations_required: 12,
    min_transaction_amount: '0.000000000000000001',
    max_transaction_amount: '1000000000'
  },
  cardano: {
    name: 'cardano',
    rpc_url: process.env['CARDANO_RPC_URL'] || 'http://cardano-node:3001',
    confirmations_required: 15,
    min_transaction_amount: '1.000000',
    max_transaction_amount: '45000000000'
  },
  polkadot: {
    name: 'polkadot',
    rpc_url: process.env['POLKADOT_RPC_URL'] || 'ws://polkadot:9944',
    confirmations_required: 6,
    min_transaction_amount: '0.0000000001',
    max_transaction_amount: '1000000000'
  }
};

/**
 * Get network configuration for a specific blockchain
 */
export function getNetworkConfig(blockchain: string): BlockchainConfig | undefined {
  return NETWORK_CONFIGS[blockchain];
}

/**
 * Get all supported blockchain networks
 */
export function getSupportedNetworks(): string[] {
  return Object.keys(NETWORK_CONFIGS);
}

/**
 * Validate if a blockchain is supported
 */
export function isSupportedBlockchain(blockchain: string): boolean {
  return blockchain in NETWORK_CONFIGS;
}