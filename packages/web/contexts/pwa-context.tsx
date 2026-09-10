'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface PWAContextType {
  isOnline: boolean;
  isInstalled: boolean;
  isInstallable: boolean;
  installApp: () => Promise<void>;
  subscribeToNotifications: () => Promise<PushSubscription | null>;
  cacheUserData: (data: any) => Promise<void>;
}

const PWAContext = createContext<PWAContextType | undefined>(undefined);

interface PWAProviderProps {
  children: ReactNode;
}

export function PWAProvider({ children }: PWAProviderProps) {
  const [isOnline, setIsOnline] = useState(true);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);

  useEffect(() => {
    // Monitor online status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    setIsOnline(navigator.onLine);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const installApp = async () => {
    console.log('Install app functionality not implemented yet');
  };

  const subscribeToNotifications = async (): Promise<PushSubscription | null> => {
    console.log('Notification subscription not implemented yet');
    return null;
  };

  const cacheUserData = async (data: any) => {
    console.log('User data caching not implemented yet');
  };

  const contextValue: PWAContextType = {
    isOnline,
    isInstalled,
    isInstallable,
    installApp,
    subscribeToNotifications,
    cacheUserData,
  };

  return (
    <PWAContext.Provider value={contextValue}>
      {children}
    </PWAContext.Provider>
  );
}

export function usePWAContext() {
  const context = useContext(PWAContext);
  if (context === undefined) {
    throw new Error('usePWAContext must be used within a PWAProvider');
  }
  return context;
}