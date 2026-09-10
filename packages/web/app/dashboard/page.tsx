'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { authManager } from '@/lib/auth';
import { apiClient } from '@/lib/api';
import { User } from '@sound-pesa/shared/types/user';
import { WalletProvider } from '@/contexts/wallet-context';
import { WalletDashboard } from '@/components/wallet/wallet-dashboard';
import { SendTransactionForm } from '@/components/wallet/send-transaction-form';
import { TransactionHistory } from '@/components/wallet/transaction-history';
import { ReceiveAddressModal } from '@/components/wallet/receive-address-modal';
import { BlockchainNetwork } from '@sound-pesa/shared/types/blockchain';
import { NotificationSettings } from '@/components/ui/pwa-notifications';
import { usePWAContext } from '@/contexts/pwa-context';

function DashboardContent() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeView, setActiveView] = useState<'overview' | 'send' | 'history' | 'settings'>('overview');
  const [selectedBlockchain, setSelectedBlockchain] = useState<BlockchainNetwork | null>(null);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const { cacheUserData, isOnline } = usePWAContext();

  useEffect(() => {
    const loadUser = async () => {
      if (!authManager.isAuthenticated()) {
        router.push('/auth/login');
        return;
      }

      try {
        const userData = authManager.getUser();
        setUser(userData);
        
        // Cache user data for offline access
        if (userData && isOnline) {
          await cacheUserData({ user: userData });
        }
      } catch (error) {
        console.error('Failed to load user:', error);
        authManager.clearAuth();
        router.push('/auth/login');
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, [router, cacheUserData, isOnline]);

  const handleLogout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
    router.push('/');
  };

  const handleSendTransaction = (blockchain: BlockchainNetwork) => {
    setSelectedBlockchain(blockchain);
    setActiveView('send');
  };

  const handleReceiveAddress = (blockchain: BlockchainNetwork) => {
    setSelectedBlockchain(blockchain);
    setShowReceiveModal(true);
  };

  const handleTransactionSuccess = () => {
    setActiveView('overview');
    setSelectedBlockchain(null);
  };

  const handleCancelTransaction = () => {
    setActiveView('overview');
    setSelectedBlockchain(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4 sm:py-6">
            <div className="flex items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
              <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 truncate">Sound Pesa</h1>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              <span className="hidden sm:block text-slate-600 truncate">
                Welcome, {user.first_name || user.username}!
              </span>
              <div className="flex items-center space-x-2">
                <Link href="/profile">
                  <Button variant="outline" size="sm">
                    <span className="hidden sm:inline">Profile</span>
                    <svg className="w-4 h-4 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </Button>
                </Link>
                <Button onClick={handleLogout} variant="outline" size="sm">
                  <span className="hidden sm:inline">Logout</span>
                  <svg className="w-4 h-4 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200 sticky top-16 sm:top-20 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-4 sm:space-x-8 overflow-x-auto">
            <button
              onClick={() => setActiveView('overview')}
              className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeView === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <svg className="w-4 h-4 inline mr-2 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
              Overview
            </button>
            <button
              onClick={() => setActiveView('send')}
              className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeView === 'send'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <svg className="w-4 h-4 inline mr-2 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Send
            </button>
            <button
              onClick={() => setActiveView('history')}
              className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeView === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <svg className="w-4 h-4 inline mr-2 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              History
            </button>
            <button
              onClick={() => setActiveView('settings')}
              className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeView === 'settings'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <svg className="w-4 h-4 inline mr-2 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        <div className="space-y-6">
          {activeView === 'overview' && (
            <div className="space-y-8">
              {/* Account Status */}
              <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 sm:p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Account Status</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
                  <div className="lg:col-span-2 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
                      <span className="text-slate-600 text-sm sm:text-base">Email:</span>
                      <span className="font-medium text-sm sm:text-base break-all">{user.email}</span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
                      <span className="text-slate-600 text-sm sm:text-base">Two-Factor Auth:</span>
                      <span className={`font-medium text-sm sm:text-base ${user.two_factor_enabled ? 'text-green-600' : 'text-red-600'}`}>
                        {user.two_factor_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
                      <span className="text-slate-600 text-sm sm:text-base">KYC Status:</span>
                      <span className={`font-medium text-sm sm:text-base capitalize ${
                        user.kyc_status === 'approved' ? 'text-green-600' : 
                        user.kyc_status === 'pending' ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {user.kyc_status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <Link href="/profile" className="block">
                      <Button variant="outline" className="w-full text-sm">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Manage Profile
                      </Button>
                    </Link>
                    {!user.two_factor_enabled && (
                      <Link href="/profile/2fa" className="block">
                        <Button variant="default" className="w-full text-sm">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                          </svg>
                          Enable 2FA
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              </div>

              {/* Wallet Dashboard */}
              <WalletDashboard
                onSendTransaction={handleSendTransaction}
                onReceiveAddress={handleReceiveAddress}
              />
            </div>
          )}

          {activeView === 'send' && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 sm:p-6">
                <SendTransactionForm
                  initialBlockchain={selectedBlockchain || undefined}
                  onSuccess={handleTransactionSuccess}
                  onCancel={handleCancelTransaction}
                />
              </div>
            </div>
          )}

          {activeView === 'history' && (
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 sm:p-6">
              <TransactionHistory />
            </div>
          )}

          {activeView === 'settings' && (
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 sm:p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">App Settings</h3>
                <NotificationSettings />
              </div>
              
              {!isOnline && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <div className="text-blue-800">
                      <p className="font-medium text-sm">Offline Mode Active</p>
                      <p className="text-xs">You're viewing cached data. Connect to internet to sync latest information.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Receive Address Modal */}
      {showReceiveModal && selectedBlockchain && (
        <ReceiveAddressModal
          blockchain={selectedBlockchain}
          isOpen={showReceiveModal}
          onClose={() => {
            setShowReceiveModal(false);
            setSelectedBlockchain(null);
          }}
        />
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <WalletProvider>
      <DashboardContent />
    </WalletProvider>
  );
}