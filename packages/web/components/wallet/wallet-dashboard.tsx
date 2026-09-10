'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useWallet } from '@/contexts/wallet-context';
import { BlockchainNetwork } from '@sound-pesa/shared/types/blockchain';

const BLOCKCHAIN_INFO = {
  bitcoin: {
    name: 'Bitcoin',
    symbol: 'BTC',
    color: 'bg-orange-500',
    textColor: 'text-orange-600',
  },
  ethereum: {
    name: 'Ethereum',
    symbol: 'ETH',
    color: 'bg-blue-500',
    textColor: 'text-blue-600',
  },
  cardano: {
    name: 'Cardano',
    symbol: 'ADA',
    color: 'bg-green-500',
    textColor: 'text-green-600',
  },
  polkadot: {
    name: 'Polkadot',
    symbol: 'DOT',
    color: 'bg-pink-500',
    textColor: 'text-pink-600',
  },
};

interface WalletCardProps {
  blockchain: BlockchainNetwork;
  onSend: (blockchain: BlockchainNetwork) => void;
  onReceive: (blockchain: BlockchainNetwork) => void;
}

function WalletCard({ blockchain, onSend, onReceive }: WalletCardProps) {
  const { balances, refreshBalance } = useWallet();
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const info = BLOCKCHAIN_INFO[blockchain];
  const balance = balances[blockchain];

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshBalance(blockchain);
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatBalance = (balance: string) => {
    const num = parseFloat(balance);
    if (num === 0) return '0.00';
    if (num < 0.01) return '< 0.01';
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 8 
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 sm:p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full ${info.color} flex items-center justify-center flex-shrink-0`}>
            <span className="text-white font-bold text-sm sm:text-base">
              {info.symbol.charAt(0)}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-slate-900 truncate">{info.name}</h3>
            <p className="text-sm text-slate-500">{info.symbol}</p>
          </div>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          loading={isRefreshing}
          className="text-slate-500 hover:text-slate-700 flex-shrink-0"
          aria-label={`Refresh ${info.name} balance`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </Button>
      </div>

      <div className="mb-6">
        <div className="text-xl sm:text-2xl font-bold text-slate-900 mb-1 break-all">
          {balance ? formatBalance(balance.balance) : '---'}
          <span className="text-base sm:text-lg font-normal text-slate-500 ml-2">{info.symbol}</span>
        </div>
        
        {balance && (
          <div className="text-sm text-slate-500 space-y-1">
            <div className="flex justify-between items-center">
              <span>Confirmed:</span>
              <span className="font-medium break-all text-right">{formatBalance(balance.confirmed_balance)} {info.symbol}</span>
            </div>
            {parseFloat(balance.unconfirmed_balance) > 0 && (
              <div className="flex justify-between items-center">
                <span>Pending:</span>
                <span className="font-medium break-all text-right">{formatBalance(balance.unconfirmed_balance)} {info.symbol}</span>
              </div>
            )}
            <div className="text-xs text-slate-400 mt-2">
              Last updated: {new Date(balance.last_updated).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
        <Button
          onClick={() => onSend(blockchain)}
          className="flex-1 w-full"
          size="sm"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          Send
        </Button>
        <Button
          onClick={() => onReceive(blockchain)}
          variant="outline"
          className="flex-1 w-full"
          size="sm"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v14m7-7l-7 7-7-7" />
          </svg>
          Receive
        </Button>
      </div>
    </div>
  );
}

interface WalletDashboardProps {
  onSendTransaction: (blockchain: BlockchainNetwork) => void;
  onReceiveAddress: (blockchain: BlockchainNetwork) => void;
}

export function WalletDashboard({ onSendTransaction, onReceiveAddress }: WalletDashboardProps) {
  const { wallets, isLoading, error, refreshAllBalances } = useWallet();
  const [isRefreshingAll, setIsRefreshingAll] = useState(false);

  const handleRefreshAll = async () => {
    setIsRefreshingAll(true);
    try {
      await refreshAllBalances();
    } finally {
      setIsRefreshingAll(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900">Your Wallets</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 sm:p-6 animate-pulse">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-slate-200 flex-shrink-0"></div>
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="h-4 bg-slate-200 rounded w-20"></div>
                  <div className="h-3 bg-slate-200 rounded w-12"></div>
                </div>
              </div>
              <div className="space-y-2 mb-6">
                <div className="h-6 sm:h-8 bg-slate-200 rounded w-32"></div>
                <div className="h-4 bg-slate-200 rounded w-24"></div>
              </div>
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                <div className="h-8 bg-slate-200 rounded flex-1"></div>
                <div className="h-8 bg-slate-200 rounded flex-1"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="text-red-800">{error}</span>
        </div>
      </div>
    );
  }

  const blockchains: BlockchainNetwork[] = ['bitcoin', 'ethereum', 'cardano', 'polkadot'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900">Your Wallets</h2>
        <Button
          onClick={handleRefreshAll}
          variant="outline"
          size="sm"
          loading={isRefreshingAll}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh All
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        {blockchains.map((blockchain) => (
          <WalletCard
            key={blockchain}
            blockchain={blockchain}
            onSend={onSendTransaction}
            onReceive={onReceiveAddress}
          />
        ))}
      </div>
    </div>
  );
}