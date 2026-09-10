'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { usePWA } from '@/hooks/use-pwa';

interface NotificationSettingsProps {
  onSettingsChange?: (enabled: boolean) => void;
}

export function NotificationSettings({ onSettingsChange }: NotificationSettingsProps) {
  const {
    isNotificationSupported,
    notificationPermission,
    requestNotificationPermission,
    subscribeToNotifications,
    unsubscribeFromNotifications,
  } = usePWA();

  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkSubscriptionStatus();
  }, []);

  const checkSubscriptionStatus = async () => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        setIsSubscribed(!!subscription);
      } catch (error) {
        console.error('Failed to check subscription status:', error);
      }
    }
  };

  const handleToggleNotifications = async () => {
    setIsLoading(true);
    
    try {
      if (isSubscribed) {
        const success = await unsubscribeFromNotifications();
        if (success) {
          setIsSubscribed(false);
          onSettingsChange?.(false);
        }
      } else {
        const subscription = await subscribeToNotifications();
        if (subscription) {
          setIsSubscribed(true);
          onSettingsChange?.(true);
        }
      }
    } catch (error) {
      console.error('Failed to toggle notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isNotificationSupported) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-yellow-800 text-sm">
            Push notifications are not supported in this browser.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Push Notifications</h3>
          <p className="text-sm text-slate-500">
            Get notified about transaction confirmations and important updates
          </p>
        </div>
        
        <Button
          onClick={handleToggleNotifications}
          loading={isLoading}
          variant={isSubscribed ? 'outline' : 'default'}
          disabled={notificationPermission === 'denied'}
        >
          {isSubscribed ? 'Disable' : 'Enable'}
        </Button>
      </div>

      {notificationPermission === 'denied' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="text-sm text-red-800">
              <p className="font-medium">Notifications are blocked</p>
              <p>Please enable notifications in your browser settings to receive updates.</p>
            </div>
          </div>
        </div>
      )}

      {isSubscribed && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-green-800 text-sm font-medium">
              You'll receive notifications for transaction updates
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// Test notification component
export function TestNotification() {
  const [isLoading, setIsLoading] = useState(false);

  const sendTestNotification = async () => {
    setIsLoading(true);
    
    try {
      // Check if notifications are supported and permitted
      if (!('Notification' in window)) {
        alert('This browser does not support notifications');
        return;
      }

      if (Notification.permission === 'granted') {
        new Notification('Sound Pesa Test', {
          body: 'This is a test notification from Sound Pesa',
          icon: '/icons/icon-192x192.png',
          badge: '/icons/icon-72x72.png',
          tag: 'test-notification',
          requireInteraction: false,
        });
      } else if (Notification.permission === 'default') {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
          new Notification('Sound Pesa Test', {
            body: 'Notifications are now enabled!',
            icon: '/icons/icon-192x192.png',
          });
        }
      } else {
        alert('Notifications are blocked. Please enable them in your browser settings.');
      }
    } catch (error) {
      console.error('Failed to send test notification:', error);
      alert('Failed to send test notification');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      onClick={sendTestNotification}
      loading={isLoading}
      variant="outline"
      size="sm"
    >
      Test Notification
    </Button>
  );
}

// Transaction notification utility
export function showTransactionNotification(
  type: 'confirmed' | 'failed' | 'pending',
  transactionId: string,
  amount?: string,
  blockchain?: string
) {
  if (!('Notification' in window) || Notification.permission !== 'granted') {
    return;
  }

  const titles = {
    confirmed: 'Transaction Confirmed',
    failed: 'Transaction Failed',
    pending: 'Transaction Pending',
  };

  const bodies = {
    confirmed: `Your ${amount ? `${amount} ` : ''}${blockchain || ''} transaction has been confirmed`,
    failed: `Your ${amount ? `${amount} ` : ''}${blockchain || ''} transaction has failed`,
    pending: `Your ${amount ? `${amount} ` : ''}${blockchain || ''} transaction is being processed`,
  };

  const icons = {
    confirmed: '/icons/icon-192x192.png',
    failed: '/icons/icon-192x192.png',
    pending: '/icons/icon-192x192.png',
  };

  new Notification(titles[type], {
    body: bodies[type],
    icon: icons[type],
    badge: '/icons/icon-72x72.png',
    tag: `transaction-${transactionId}`,
    data: {
      type: `transaction_${type}`,
      transactionId,
    },
    requireInteraction: type === 'failed',
  } as NotificationOptions);
}