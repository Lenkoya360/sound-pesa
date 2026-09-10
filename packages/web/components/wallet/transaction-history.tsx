'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { apiClient } from '@/lib/api';
import { 
  BlockchainNetwork 
} from '@sound-pesa/shared/types/blockchain';
import { 
  Transaction, 
  TransactionHistory as TransactionHistoryType,
  TransactionStatus 
} from '@sound-pesa/shared/types/transaction';

const BLOCKCHAIN_OPTIONS = [
  { value: '', label: 'All Blockchains' },
  { value: 'bitcoin', label: 'Bitcoin (BTC)' },
  { value: 'ethereum', label: 'Ethereum (ETH)' },
  { value: 'cardano', label: 'Cardano (ADA)' },
  { value: 'polkadot', label: 'Polkadot (DOT)' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

interface TransactionRowProps {
  transaction: Transaction;
}

function TransactionRow({ transaction }: TransactionRowProps) {
  const getStatusColor = (status: TransactionStatus) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatAmount = (amount: string) => {
    const num = parseFloat(amount);
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 8 
    });
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleString();
  };

  const truncateAddress = (address: string) => {
    if (address.length <= 12) return address;
    return `${address.slice(0, 6)}...${address.slice(-6)}`;
  };

  const truncateHash = (hash?: string) => {
    if (!hash) return 'N/A';
    if (hash.length <= 12) return hash;
    return `${hash.slice(0, 6)}...${hash.slice(-6)}`;
  };

  return (
    <tr className="hover:bg-slate-50">
      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
        {formatDate(transaction.created_at)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className="text-sm font-medium text-slate-900 capitalize">
          {transaction.blockchain}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
        {truncateAddress(transaction.to_address)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
        {formatAmount(transaction.amount)} {transaction.blockchain.toUpperCase()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
        {formatAmount(transaction.fee)} {transaction.blockchain.toUpperCase()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(transaction.status)}`}>
          {transaction.status}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
        {transaction.confirmations}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
        {truncateHash(transaction.transaction_hash)}
      </td>
    </tr>
  );
}

interface TransactionHistoryProps {
  selectedBlockchain?: BlockchainNetwork;
}

export function TransactionHistory({ selectedBlockchain }: TransactionHistoryProps) {
  const [history, setHistory] = useState<TransactionHistoryType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [filters, setFilters] = useState({
    blockchain: selectedBlockchain || '' as BlockchainNetwork | '',
    status: '' as TransactionStatus | '',
  });
  
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const loadTransactions = async (page = 1) => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (filters.blockchain) {
        // Load transactions for specific blockchain
        const data = await apiClient.getWalletHistory(filters.blockchain, page, pageSize);
        setHistory(data);
      } else {
        // For "All Blockchains", we need to load from each blockchain and combine
        // This is a simplified approach - in a real app, you'd have a unified endpoint
        const blockchains: BlockchainNetwork[] = ['bitcoin', 'ethereum', 'cardano', 'polkadot'];
        const allTransactions: Transaction[] = [];
        
        for (const blockchain of blockchains) {
          try {
            const data = await apiClient.getWalletHistory(blockchain, 1, 100);
            allTransactions.push(...data.transactions);
          } catch (err) {
            // Continue if one blockchain fails
            console.warn(`Failed to load ${blockchain} transactions:`, err);
          }
        }
        
        // Sort by date (newest first)
        allTransactions.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        
        // Apply status filter
        const filteredTransactions = filters.status 
          ? allTransactions.filter(tx => tx.status === filters.status)
          : allTransactions;
        
        // Paginate
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex);
        
        setHistory({
          transactions: paginatedTransactions,
          total_count: filteredTransactions.length,
          page,
          page_size: pageSize,
          has_next: endIndex < filteredTransactions.length,
          has_previous: page > 1,
        });
      }
    } catch (err: any) {
      console.error('Failed to load transaction history:', err);
      setError(err.message || 'Failed to load transaction history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setCurrentPage(1);
    loadTransactions(1);
  }, [filters.blockchain, filters.status]);

  useEffect(() => {
    loadTransactions(currentPage);
  }, [currentPage]);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handleRefresh = () => {
    loadTransactions(currentPage);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-red-800">{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <div className="px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Transaction History</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            loading={isLoading}
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        </div>
        
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Blockchain"
            options={BLOCKCHAIN_OPTIONS}
            value={filters.blockchain}
            onChange={(e) => setFilters(prev => ({ 
              ...prev, 
              blockchain: e.target.value as BlockchainNetwork | '' 
            }))}
          />
          <Select
            label="Status"
            options={STATUS_OPTIONS}
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ 
              ...prev, 
              status: e.target.value as TransactionStatus | '' 
            }))}
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Blockchain
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                To Address
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Fee
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Confirmations
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Tx Hash
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {isLoading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-24"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-16"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-20"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-16"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-12"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-6 bg-slate-200 rounded-full w-16"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-8"></div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="h-4 bg-slate-200 rounded w-20"></div>
                  </td>
                </tr>
              ))
            ) : history?.transactions.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center">
                  <div className="text-slate-500">
                    <svg className="mx-auto h-12 w-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p className="text-sm">No transactions found</p>
                  </div>
                </td>
              </tr>
            ) : (
              history?.transactions.map((transaction) => (
                <TransactionRow key={transaction.id} transaction={transaction} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {history && history.total_count > 0 && (
        <div className="px-6 py-4 border-t border-slate-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-slate-700">
              Showing {((history.page - 1) * history.page_size) + 1} to{' '}
              {Math.min(history.page * history.page_size, history.total_count)} of{' '}
              {history.total_count} transactions
            </div>
            
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={!history.has_previous}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={!history.has_next}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}