'use client';

import { PWAProvider } from '@/contexts/pwa-context';

interface PWAInitProps {
  children: React.ReactNode;
}

export function PWAInit({ children }: PWAInitProps) {
  return (
    <PWAProvider>
      {children}
    </PWAProvider>
  );
}