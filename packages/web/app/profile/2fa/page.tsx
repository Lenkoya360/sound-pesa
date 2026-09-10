'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import QRCode from 'qrcode';
import { FormInput } from '@/components/ui/form-input';
import { Button } from '@/components/ui/button';
import { twoFactorSchema, TwoFactorFormData } from '@/lib/validations';
import { apiClient, APIError } from '@/lib/api';
import { authManager } from '@/lib/auth';
import { User } from '@sound-pesa/shared/types/user';

export default function TwoFactorAuthPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [step, setStep] = useState<'setup' | 'verify' | 'complete' | 'disable'>('setup');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<TwoFactorFormData>({
    resolver: zodResolver(twoFactorSchema),
  });

  useEffect(() => {
    const loadUserAndSetup = async () => {
      if (!authManager.isAuthenticated()) {
        router.push('/auth/login');
        return;
      }

      try {
        const userData = authManager.getUser();
        if (!userData) {
          router.push('/auth/login');
          return;
        }

        setUser(userData);

        if (userData.two_factor_enabled) {
          setStep('disable');
        } else {
          // Generate QR code for 2FA setup
          const response = await apiClient.enable2FA();
          setSecret(response.secret);
          
          // Generate QR code
          const qrData = `otpauth://totp/Sound%20Pesa:${userData.email}?secret=${response.secret}&issuer=Sound%20Pesa`;
          const qrCodeDataUrl = await QRCode.toDataURL(qrData);
          setQrCodeUrl(qrCodeDataUrl);
          setStep('verify');
        }
      } catch (error) {
        if (error instanceof APIError && error.status === 401) {
          authManager.clearAuth();
          router.push('/auth/login');
        } else {
          setApiError('Failed to load 2FA setup');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUserAndSetup();
  }, [router]);

  const onVerify2FA = async (data: TwoFactorFormData) => {
    setIsProcessing(true);
    setApiError(null);

    try {
      const response = await apiClient.verify2FA(data.code);
      setBackupCodes(response.backup_codes);
      
      // Update user state
      const updatedUser = { ...user!, two_factor_enabled: true };
      setUser(updatedUser);
      authManager.setUser(updatedUser);
      
      setStep('complete');
    } catch (error) {
      if (error instanceof APIError) {
        if (error.code === 'AUTH_INVALID_2FA_CODE') {
          setError('code', { message: 'Invalid verification code. Please try again.' });
        } else {
          setApiError(error.message);
        }
      } else {
        setApiError('Failed to verify 2FA code');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const onDisable2FA = async (data: TwoFactorFormData) => {
    setIsProcessing(true);
    setApiError(null);

    try {
      await apiClient.disable2FA(data.code);
      
      // Update user state
      const updatedUser = { ...user!, two_factor_enabled: false };
      setUser(updatedUser);
      authManager.setUser(updatedUser);
      
      router.push('/profile?message=2fa-disabled');
    } catch (error) {
      if (error instanceof APIError) {
        if (error.code === 'AUTH_INVALID_2FA_CODE') {
          setError('code', { message: 'Invalid verification code. Please try again.' });
        } else {
          setApiError(error.message);
        }
      } else {
        setApiError('Failed to disable 2FA');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-slate-600">Loading 2FA setup...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-slate-200">
            <h1 className="text-2xl font-bold text-slate-900">
              {step === 'disable' ? 'Disable Two-Factor Authentication' : 'Setup Two-Factor Authentication'}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              {step === 'disable' 
                ? 'Enter your 2FA code to disable two-factor authentication'
                : 'Secure your account with two-factor authentication'
              }
            </p>
          </div>

          <div className="p-6">
            {apiError && (
              <div className="mb-6 rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-700">{apiError}</div>
              </div>
            )}

            {step === 'verify' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">
                    Scan QR Code with your Authenticator App
                  </h3>
                  
                  {qrCodeUrl && (
                    <div className="flex justify-center mb-4">
                      <img src={qrCodeUrl} alt="2FA QR Code" className="border rounded-lg" />
                    </div>
                  )}
                  
                  <p className="text-sm text-slate-600 mb-4">
                    Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                  </p>
                  
                  {secret && (
                    <div className="bg-slate-50 p-4 rounded-lg">
                      <p className="text-sm font-medium text-slate-700 mb-2">
                        Can't scan? Enter this code manually:
                      </p>
                      <code className="text-sm bg-white px-2 py-1 rounded border font-mono">
                        {secret}
                      </code>
                    </div>
                  )}
                </div>

                <form onSubmit={handleSubmit(onVerify2FA)} className="space-y-4">
                  <FormInput
                    {...register('code')}
                    type="text"
                    label="Verification Code"
                    placeholder="Enter 6-digit code"
                    error={errors.code?.message}
                    maxLength={6}
                    helperText="Enter the 6-digit code from your authenticator app"
                  />

                  <div className="flex space-x-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => router.push('/profile')}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      loading={isProcessing}
                      disabled={isProcessing}
                    >
                      {isProcessing ? 'Verifying...' : 'Verify & Enable'}
                    </Button>
                  </div>
                </form>
              </div>
            )}

            {step === 'complete' && (
              <div className="text-center space-y-6">
                <div className="text-green-600">
                  <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-2">
                    Two-Factor Authentication Enabled!
                  </h3>
                  <p className="text-slate-600">
                    Your account is now protected with two-factor authentication.
                  </p>
                </div>

                {backupCodes && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-800 mb-2">
                      Save Your Backup Codes
                    </h4>
                    <p className="text-sm text-yellow-700 mb-4">
                      Store these backup codes in a safe place. You can use them to access your account if you lose your authenticator device.
                    </p>
                    <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                      {backupCodes.map((code, index) => (
                        <div key={index} className="bg-white px-2 py-1 rounded border">
                          {code}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Button onClick={() => router.push('/profile')}>
                  Return to Profile
                </Button>
              </div>
            )}

            {step === 'disable' && (
              <div className="space-y-6">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="font-medium text-red-800 mb-2">
                    Disable Two-Factor Authentication
                  </h3>
                  <p className="text-sm text-red-700">
                    Disabling 2FA will make your account less secure. Are you sure you want to continue?
                  </p>
                </div>

                <form onSubmit={handleSubmit(onDisable2FA)} className="space-y-4">
                  <FormInput
                    {...register('code')}
                    type="text"
                    label="Verification Code"
                    placeholder="Enter 6-digit code"
                    error={errors.code?.message}
                    maxLength={6}
                    helperText="Enter the 6-digit code from your authenticator app to confirm"
                  />

                  <div className="flex space-x-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => router.push('/profile')}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="destructive"
                      loading={isProcessing}
                      disabled={isProcessing}
                    >
                      {isProcessing ? 'Disabling...' : 'Disable 2FA'}
                    </Button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}