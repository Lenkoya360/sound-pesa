'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiClient } from '@/lib/api';
import { useWebSocket, WebSocketMessage } from '@/hooks/use-websocket';
import { 
  Wallet, 
  WalletBalance, 
  BlockchainNetwork 
} from '@sound-pesa/shared/types/blockchain';
import { Transaction } from '@sound-pesa/shared/types/transaction';

interface WalletContextType {
  wallets: Wallet[];
  balances: Record<string, WalletBalance>;
  isLoading: boolean;
  error: string | null;
  refreshWallets: () => Promise<void>;
  refreshBalance: (blockchain: BlockchainNetwork) => Promise<void>;
  refreshAllBalances: () => Promise<void>;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export function useWallet() {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
}

interface WalletProviderProps {
  children: ReactNode;
}

export function WalletProvider({ children }: WalletProviderProps) {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [balances, setBalances] = useState<Record<string, WalletBalance>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'balance_update':
        const { blockchain, balance } = message.data;
        setBalances(prev => ({
          ...prev,
          [blockchain]: balance,
        }));
        break;
      
      case 'transaction_update':
        // Refresh balances when transaction status changes
        const transaction: Transaction = message.data;
        refreshBalance(transaction.blockchain);
        break;
      
      default:
        break;
    }
  };

  const { isConnected } = useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  const refreshWallets = async () => {
    try {
      setError(null);
      const walletsData = await apiClient.getWallets();
      setWallets(walletsData);
    } catch (err) {
      console.error('Failed to fetch wallets:', err);
      setError('Failed to load wallets');
    }
  };

  const refreshBalance = async (blockchain: BlockchainNetwork) => {
    try {
      const balance = await apiClient.getWalletBalance(blockchain);
      setBalances(prev => ({
        ...prev,
        [blockchain]: balance,
      }));
    } catch (err) {
      console.error(`Failed to fetch ${blockchain} balance:`, err);
    }
  };

  const refreshAllBalances = async () => {
    const blockchains: BlockchainNetwork[] = ['bitcoin', 'ethereum', 'cardano', 'polkadot'];
    
    await Promise.all(
      blockchains.map(blockchain => refreshBalance(blockchain))
    );
  };

  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      try {
        await refreshWallets();
        await refreshAllBalances();
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const value: WalletContextType = {
    wallets,
    balances,
    isLoading,
    error,
    refreshWallets,
    refreshBalance,
    refreshAllBalances,
  };

  return (
    <WalletContext.Provider value={value}>
      {children}
    </WalletContext.Provider>
  );
}