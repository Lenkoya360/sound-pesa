'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { FormInput } from '@/components/ui/form-input';
import { Select } from '@/components/ui/select';
import { apiClient } from '@/lib/api';
import { useWallet } from '@/contexts/wallet-context';
import { 
  BlockchainNetwork, 
  Wallet 
} from '@sound-pesa/shared/types/blockchain';
import { 
  TransactionEstimate, 
  TransactionSendRequest 
} from '@sound-pesa/shared/types/transaction';

const BLOCKCHAIN_OPTIONS = [
  { value: 'bitcoin', label: 'Bitcoin (BTC)' },
  { value: 'ethereum', label: 'Ethereum (ETH)' },
  { value: 'cardano', label: 'Cardano (ADA)' },
  { value: 'polkadot', label: 'Polkadot (DOT)' },
];

const FEE_PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low (Slower, Cheaper)' },
  { value: 'medium', label: 'Medium (Recommended)' },
  { value: 'high', label: 'High (Faster, More Expensive)' },
];

interface SendTransactionFormProps {
  initialBlockchain?: BlockchainNetwork;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function SendTransactionForm({ 
  initialBlockchain, 
  onSuccess, 
  onCancel 
}: SendTransactionFormProps) {
  const { wallets, balances } = useWallet();
  
  const [formData, setFormData] = useState({
    blockchain: initialBlockchain || '' as BlockchainNetwork,
    toAddress: '',
    amount: '',
    feePriority: 'medium' as 'low' | 'medium' | 'high',
  });
  
  const [estimate, setEstimate] = useState<TransactionEstimate | null>(null);
  const [isEstimating, setIsEstimating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedWallet = wallets.find(w => w.blockchain === formData.blockchain);
  const selectedBalance = formData.blockchain ? balances[formData.blockchain] : null;

  const validateAddress = (address: string, blockchain: BlockchainNetwork): boolean => {
    if (!address) return false;
    
    // Basic validation patterns for each blockchain
    const patterns = {
      bitcoin: /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$/,
      ethereum: /^0x[a-fA-F0-9]{40}$/,
      cardano: /^addr1[a-z0-9]{98}$/,
      polkadot: /^1[a-zA-Z0-9]{46}$/,
    };
    
    return patterns[blockchain]?.test(address) || false;
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.blockchain) {
      newErrors.blockchain = 'Please select a blockchain';
    }

    if (!formData.toAddress) {
      newErrors.toAddress = 'Recipient address is required';
    } else if (!validateAddress(formData.toAddress, formData.blockchain)) {
      newErrors.toAddress = 'Invalid address format for selected blockchain';
    }

    if (!formData.amount) {
      newErrors.amount = 'Amount is required';
    } else {
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        newErrors.amount = 'Amount must be a positive number';
      } else if (selectedBalance && amount > parseFloat(selectedBalance.confirmed_balance)) {
        newErrors.amount = 'Insufficient balance';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const estimateFee = async () => {
    if (!formData.blockchain || !formData.toAddress || !formData.amount) {
      return;
    }

    if (!validateAddress(formData.toAddress, formData.blockchain)) {
      return;
    }

    setIsEstimating(true);
    try {
      const estimate = await apiClient.estimateTransactionFee(
        formData.blockchain,
        formData.amount,
        formData.toAddress
      );
      setEstimate(estimate);
    } catch (error) {
      console.error('Failed to estimate fee:', error);
      setEstimate(null);
    } finally {
      setIsEstimating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !selectedWallet) {
      return;
    }

    setIsSending(true);
    try {
      const request: TransactionSendRequest = {
        from_wallet_id: selectedWallet.id,
        to_address: formData.toAddress,
        amount: formData.amount,
        blockchain: formData.blockchain,
        fee_priority: formData.feePriority,
      };

      await apiClient.sendTransaction(request);
      
      // Reset form
      setFormData({
        blockchain: '' as BlockchainNetwork,
        toAddress: '',
        amount: '',
        feePriority: 'medium',
      });
      setEstimate(null);
      setErrors({});
      
      onSuccess?.();
    } catch (error: any) {
      setErrors({
        submit: error.message || 'Failed to send transaction',
      });
    } finally {
      setIsSending(false);
    }
  };

  // Auto-estimate fee when form changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      estimateFee();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [formData.blockchain, formData.toAddress, formData.amount]);

  const formatBalance = (balance: string) => {
    const num = parseFloat(balance);
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 8 
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Send Transaction</h3>
        {onCancel && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Select
          label="Blockchain"
          options={BLOCKCHAIN_OPTIONS}
          value={formData.blockchain}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            blockchain: e.target.value as BlockchainNetwork 
          }))}
          error={errors.blockchain}
        />

        {selectedBalance && (
          <div className="bg-slate-50 rounded-lg p-3">
            <div className="text-sm text-slate-600">Available Balance:</div>
            <div className="font-semibold text-slate-900">
              {formatBalance(selectedBalance.confirmed_balance)} {formData.blockchain.toUpperCase()}
            </div>
            {parseFloat(selectedBalance.unconfirmed_balance) > 0 && (
              <div className="text-xs text-slate-500">
                + {formatBalance(selectedBalance.unconfirmed_balance)} pending
              </div>
            )}
          </div>
        )}

        <FormInput
          label="Recipient Address"
          type="text"
          value={formData.toAddress}
          onChange={(e) => setFormData(prev => ({ ...prev, toAddress: e.target.value }))}
          placeholder="Enter recipient address"
          error={errors.toAddress}
        />

        <FormInput
          label="Amount"
          type="number"
          step="any"
          value={formData.amount}
          onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
          placeholder="0.00"
          error={errors.amount}
        />

        <Select
          label="Fee Priority"
          options={FEE_PRIORITY_OPTIONS}
          value={formData.feePriority}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            feePriority: e.target.value as 'low' | 'medium' | 'high'
          }))}
        />

        {estimate && (
          <div className="bg-blue-50 rounded-lg p-4 space-y-2">
            <div className="text-sm font-medium text-blue-900">Transaction Estimate</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700">Estimated Fee:</span>
                <div className="font-semibold text-blue-900">
                  {estimate.estimated_fee} {formData.blockchain.toUpperCase()}
                </div>
              </div>
              <div>
                <span className="text-blue-700">Confirmation Time:</span>
                <div className="font-semibold text-blue-900">
                  ~{estimate.estimated_confirmation_time} min
                </div>
              </div>
            </div>
            <div className="text-xs text-blue-600">
              Network congestion: {estimate.network_congestion}
            </div>
          </div>
        )}

        {isEstimating && (
          <div className="text-center py-2">
            <div className="inline-flex items-center text-sm text-slate-600">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Estimating transaction fee...
            </div>
          </div>
        )}

        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="text-sm text-red-800">{errors.submit}</div>
          </div>
        )}

        <div className="flex space-x-3 pt-4">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="flex-1"
            >
              Cancel
            </Button>
          )}
          <Button
            type="submit"
            loading={isSending}
            disabled={!validateForm() || isEstimating}
            className="flex-1"
          >
            Send Transaction
          </Button>
        </div>
      </form>
    </div>
  );
}