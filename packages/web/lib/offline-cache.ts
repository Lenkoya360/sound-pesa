'use client';

import { User } from '@sound-pesa/shared/types/user';
import { WalletBalance } from '@sound-pesa/shared/types/blockchain';
import { Transaction } from '@sound-pesa/shared/types/transaction';

// IndexedDB database configuration
const DB_NAME = 'SoundPesaOfflineDB';
const DB_VERSION = 1;

// Store names
const STORES = {
  USER_DATA: 'userData',
  WALLET_BALANCES: 'walletBalances',
  TRANSACTIONS: 'transactions',
  SETTINGS: 'settings',
} as const;

interface OfflineCacheData {
  user?: User;
  walletBalances?: Record<string, WalletBalance>;
  recentTransactions?: Transaction[];
  lastSync?: number;
}

class OfflineCache {
  private db: IDBDatabase | null = null;
  private initPromise: Promise<void> | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.initPromise = this.initDB();
    }
  }

  private async initDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!('indexedDB' in window)) {
        reject(new Error('IndexedDB not supported'));
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        if (!db.objectStoreNames.contains(STORES.USER_DATA)) {
          db.createObjectStore(STORES.USER_DATA, { keyPath: 'id' });
        }

        if (!db.objectStoreNames.contains(STORES.WALLET_BALANCES)) {
          const walletStore = db.createObjectStore(STORES.WALLET_BALANCES, { keyPath: 'wallet_id' });
          walletStore.createIndex('blockchain', 'blockchain', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.TRANSACTIONS)) {
          const txStore = db.createObjectStore(STORES.TRANSACTIONS, { keyPath: 'id' });
          txStore.createIndex('user_id', 'user_id', { unique: false });
          txStore.createIndex('status', 'status', { unique: false });
          txStore.createIndex('created_at', 'created_at', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.SETTINGS)) {
          db.createObjectStore(STORES.SETTINGS, { keyPath: 'key' });
        }
      };
    });
  }

  private async ensureDB(): Promise<IDBDatabase> {
    if (this.initPromise) {
      await this.initPromise;
    }
    
    if (!this.db) {
      throw new Error('Database not initialized');
    }
    
    return this.db;
  }

  // User data caching
  async cacheUserData(user: User): Promise<void> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.USER_DATA], 'readwrite');
      const store = transaction.objectStore(STORES.USER_DATA);
      
      await new Promise<void>((resolve, reject) => {
        const request = store.put({ ...user, cachedAt: Date.now() });
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });

      console.log('User data cached successfully');
    } catch (error) {
      console.error('Failed to cache user data:', error);
    }
  }

  async getCachedUserData(): Promise<User | null> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.USER_DATA], 'readonly');
      const store = transaction.objectStore(STORES.USER_DATA);
      
      return new Promise<User | null>((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => {
          const users = request.result;
          if (users.length > 0) {
            const { cachedAt, ...userData } = users[0];
            resolve(userData as User);
          } else {
            resolve(null);
          }
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get cached user data:', error);
      return null;
    }
  }

  // Wallet balance caching
  async cacheWalletBalances(balances: Record<string, WalletBalance>): Promise<void> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.WALLET_BALANCES], 'readwrite');
      const store = transaction.objectStore(STORES.WALLET_BALANCES);
      
      // Clear existing balances
      await new Promise<void>((resolve, reject) => {
        const clearRequest = store.clear();
        clearRequest.onsuccess = () => resolve();
        clearRequest.onerror = () => reject(clearRequest.error);
      });

      // Add new balances
      for (const [walletId, balance] of Object.entries(balances)) {
        await new Promise<void>((resolve, reject) => {
          const request = store.put({ ...balance, wallet_id: walletId, cachedAt: Date.now() });
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
      }

      console.log('Wallet balances cached successfully');
    } catch (error) {
      console.error('Failed to cache wallet balances:', error);
    }
  }

  async getCachedWalletBalances(): Promise<Record<string, WalletBalance> | null> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.WALLET_BALANCES], 'readonly');
      const store = transaction.objectStore(STORES.WALLET_BALANCES);
      
      return new Promise<Record<string, WalletBalance> | null>((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => {
          const balances = request.result;
          if (balances.length > 0) {
            const balanceMap: Record<string, WalletBalance> = {};
            balances.forEach((balance) => {
              const { wallet_id, cachedAt, ...balanceData } = balance;
              balanceMap[wallet_id] = balanceData as WalletBalance;
            });
            resolve(balanceMap);
          } else {
            resolve(null);
          }
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get cached wallet balances:', error);
      return null;
    }
  }

  // Transaction caching
  async cacheTransactions(transactions: Transaction[]): Promise<void> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.TRANSACTIONS], 'readwrite');
      const store = transaction.objectStore(STORES.TRANSACTIONS);
      
      for (const tx of transactions) {
        await new Promise<void>((resolve, reject) => {
          const request = store.put({ ...tx, cachedAt: Date.now() });
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
      }

      console.log(`${transactions.length} transactions cached successfully`);
    } catch (error) {
      console.error('Failed to cache transactions:', error);
    }
  }

  async getCachedTransactions(limit: number = 50): Promise<Transaction[]> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.TRANSACTIONS], 'readonly');
      const store = transaction.objectStore(STORES.TRANSACTIONS);
      const index = store.index('created_at');
      
      return new Promise<Transaction[]>((resolve, reject) => {
        const request = index.openCursor(null, 'prev'); // Most recent first
        const transactions: Transaction[] = [];
        let count = 0;
        
        request.onsuccess = () => {
          const cursor = request.result;
          if (cursor && count < limit) {
            const { cachedAt, ...txData } = cursor.value;
            transactions.push(txData as Transaction);
            count++;
            cursor.continue();
          } else {
            resolve(transactions);
          }
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get cached transactions:', error);
      return [];
    }
  }

  // Settings caching
  async cacheSetting(key: string, value: any): Promise<void> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.SETTINGS], 'readwrite');
      const store = transaction.objectStore(STORES.SETTINGS);
      
      await new Promise<void>((resolve, reject) => {
        const request = store.put({ key, value, cachedAt: Date.now() });
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to cache setting:', error);
    }
  }

  async getCachedSetting(key: string): Promise<any> {
    try {
      const db = await this.ensureDB();
      const transaction = db.transaction([STORES.SETTINGS], 'readonly');
      const store = transaction.objectStore(STORES.SETTINGS);
      
      return new Promise<any>((resolve, reject) => {
        const request = store.get(key);
        request.onsuccess = () => {
          const result = request.result;
          resolve(result ? result.value : null);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get cached setting:', error);
      return null;
    }
  }

  // Cache management
  async clearCache(): Promise<void> {
    try {
      const db = await this.ensureDB();
      const storeNames = Object.values(STORES);
      const transaction = db.transaction(storeNames, 'readwrite');
      
      for (const storeName of storeNames) {
        const store = transaction.objectStore(storeName);
        await new Promise<void>((resolve, reject) => {
          const request = store.clear();
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
      }

      console.log('Cache cleared successfully');
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  async getCacheSize(): Promise<number> {
    try {
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        return estimate.usage || 0;
      }
      return 0;
    } catch (error) {
      console.error('Failed to get cache size:', error);
      return 0;
    }
  }

  // Sync status
  async setLastSyncTime(): Promise<void> {
    await this.cacheSetting('lastSync', Date.now());
  }

  async getLastSyncTime(): Promise<number | null> {
    return await this.getCachedSetting('lastSync');
  }

  // Check if data is stale (older than 5 minutes)
  isDataStale(cachedAt: number, maxAge: number = 5 * 60 * 1000): boolean {
    return Date.now() - cachedAt > maxAge;
  }
}

// Export singleton instance
export const offlineCache = new OfflineCache();

// Utility functions for common operations
export async function cacheEssentialUserData(data: OfflineCacheData): Promise<void> {
  const promises: Promise<void>[] = [];

  if (data.user) {
    promises.push(offlineCache.cacheUserData(data.user));
  }

  if (data.walletBalances) {
    promises.push(offlineCache.cacheWalletBalances(data.walletBalances));
  }

  if (data.recentTransactions) {
    promises.push(offlineCache.cacheTransactions(data.recentTransactions));
  }

  await Promise.all(promises);
  await offlineCache.setLastSyncTime();
}

export async function getCachedEssentialData(): Promise<OfflineCacheData> {
  const [user, walletBalances, recentTransactions, lastSync] = await Promise.all([
    offlineCache.getCachedUserData(),
    offlineCache.getCachedWalletBalances(),
    offlineCache.getCachedTransactions(20),
    offlineCache.getLastSyncTime(),
  ]);

  return {
    user: user || undefined,
    walletBalances: walletBalances || undefined,
    recentTransactions,
    lastSync: lastSync || undefined,
  };
}