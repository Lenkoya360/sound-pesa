// Transaction types
import { BlockchainNetwork } from './blockchain';

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
  created_at: Date;
}

export type TransactionStatus = 'pending' | 'confirmed' | 'failed' | 'cancelled';