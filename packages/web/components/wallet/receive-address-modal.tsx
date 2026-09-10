'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useWallet } from '@/contexts/wallet-context';
import { BlockchainNetwork } from '@sound-pesa/shared/types/blockchain';

interface ReceiveAddressModalProps {
  blockchain: BlockchainNetwork;
  isOpen: boolean;
  onClose: () => void;
}

export function ReceiveAddressModal({ blockchain, isOpen, onClose }: ReceiveAddressModalProps) {
  const { wallets } = useWallet();
  const [copied, setCopied] = useState(false);

  const wallet = wallets.find(w => w.blockchain === blockchain);

  const handleCopyAddress = async () => {
    if (!wallet?.address) return;

    try {
      await navigator.clipboard.writeText(wallet.address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy address:', error);
    }
  };

  const generateQRCode = (address: string) => {
    // In a real implementation, you'd use a QR code library like qrcode
    // For now, we'll use a placeholder QR code service
    return `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(address)}`;
  };

  if (!isOpen) return null;

  const blockchainInfo = {
    bitcoin: { name: 'Bitcoin', symbol: 'BTC', color: 'bg-orange-500' },
    ethereum: { name: 'Ethereum', symbol: 'ETH', color: 'bg-blue-500' },
    cardano: { name: 'Cardano', symbol: 'ADA', color: 'bg-green-500' },
    polkadot: { name: 'Polkadot', symbol: 'DOT', color: 'bg-pink-500' },
  };

  const info = blockchainInfo[blockchain];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 rounded-full ${info.color} flex items-center justify-center`}>
              <span className="text-white font-bold text-sm">
                {info.symbol.charAt(0)}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Receive {info.name}
              </h3>
              <p className="text-sm text-slate-500">Share this address to receive {info.symbol}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </div>

        <div className="p-6">
          {wallet ? (
            <div className="space-y-6">
              {/* QR Code */}
              <div className="flex justify-center">
                <div className="bg-white p-4 rounded-lg border-2 border-slate-200">
                  <img
                    src={generateQRCode(wallet.address)}
                    alt="QR Code"
                    className="w-48 h-48"
                  />
                </div>
              </div>

              {/* Address */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  Your {info.name} Address
                </label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <code className="text-sm text-slate-900 break-all">
                      {wallet.address}
                    </code>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyAddress}
                    className={copied ? 'text-green-600 border-green-300' : ''}
                  >
                    {copied ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </Button>
                </div>
                {copied && (
                  <p className="text-sm text-green-600">Address copied to clipboard!</p>
                )}
              </div>

              {/* Warning */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-yellow-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium mb-1">Important:</p>
                    <ul className="space-y-1 text-xs">
                      <li>• Only send {info.symbol} to this address</li>
                      <li>• Sending other cryptocurrencies may result in permanent loss</li>
                      <li>• Double-check the address before sharing</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p className="text-slate-600">No wallet found for {info.name}</p>
              <p className="text-sm text-slate-500 mt-1">
                Please create a wallet first to receive {info.symbol}
              </p>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-slate-200">
          <Button onClick={onClose} className="w-full">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}