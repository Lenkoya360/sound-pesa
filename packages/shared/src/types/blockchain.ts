// Blockchain and wallet types
export type BlockchainNetwork = 'bitcoin' | 'ethereum' | 'cardano' | 'polkadot';

export interface BlockchainConfig {
  name: string;
  rpc_url: string;
  confirmations_required: number;
  min_transaction_amount: string;
  max_transaction_amount: string;
  network_id?: number;
  address_prefix?: string;
}

export interface Wallet {
  id: string;
  user_id: string;
  blockchain: BlockchainNetwork;
  address: string;
  created_at: Date;
  is_active: boolean;
  label?: string;
}