'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FormInput } from '@/components/ui/form-input';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { profileSchema, ProfileFormData, changePasswordSchema, ChangePasswordFormData } from '@/lib/validations';
import { apiClient, APIError } from '@/lib/api';
import { authManager } from '@/lib/auth';
import { User } from '@sound-pesa/shared/types/user';

// Common countries list (same as registration)
const countries = [
  { value: 'US', label: 'United States' },
  { value: 'CA', label: 'Canada' },
  { value: 'GB', label: 'United Kingdom' },
  { value: 'DE', label: 'Germany' },
  { value: 'FR', label: 'France' },
  { value: 'JP', label: 'Japan' },
  { value: 'AU', label: 'Australia' },
  { value: 'BR', label: 'Brazil' },
  { value: 'IN', label: 'India' },
  { value: 'CN', label: 'China' },
  { value: 'KE', label: 'Kenya' },
  { value: 'NG', label: 'Nigeria' },
  { value: 'ZA', label: 'South Africa' },
  { value: 'EG', label: 'Egypt' },
  { value: 'GH', label: 'Ghana' },
  { value: 'UG', label: 'Uganda' },
  { value: 'TZ', label: 'Tanzania' },
  { value: 'RW', label: 'Rwanda' },
  { value: 'ET', label: 'Ethiopia' },
  { value: 'MA', label: 'Morocco' },
];

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'security'>('profile');

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
  });

  const passwordForm = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  });

  useEffect(() => {
    const loadUserProfile = async () => {
      if (!authManager.isAuthenticated()) {
        router.push('/auth/login');
        return;
      }

      try {
        const userData = await apiClient.getUserProfile();
        setUser(userData);
        
        // Set form default values
        profileForm.reset({
          firstName: userData.first_name || '',
          lastName: userData.last_name || '',
          phoneNumber: userData.phone_number || '',
          country: userData.country || '',
        });
      } catch (error) {
        if (error instanceof APIError && error.status === 401) {
          authManager.clearAuth();
          router.push('/auth/login');
        } else {
          setApiError('Failed to load profile data');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUserProfile();
  }, [router, profileForm]);

  const onUpdateProfile = async (data: ProfileFormData) => {
    setIsUpdating(true);
    setApiError(null);
    setSuccessMessage(null);

    try {
      const updatedUser = await apiClient.updateUserProfile({
        first_name: data.firstName,
        last_name: data.lastName,
        phone_number: data.phoneNumber || undefined,
        country: data.country,
      });

      setUser(updatedUser);
      authManager.setUser(updatedUser);
      setSuccessMessage('Profile updated successfully');
    } catch (error) {
      if (error instanceof APIError) {
        setApiError(error.message);
      } else {
        setApiError('Failed to update profile');
      }
    } finally {
      setIsUpdating(false);
    }
  };

  const onChangePassword = async (data: ChangePasswordFormData) => {
    setIsChangingPassword(true);
    setApiError(null);
    setSuccessMessage(null);

    try {
      await apiClient.changePassword(data.currentPassword, data.newPassword);
      setSuccessMessage('Password changed successfully');
      passwordForm.reset();
    } catch (error) {
      if (error instanceof APIError) {
        if (error.code === 'AUTH_INVALID_PASSWORD') {
          passwordForm.setError('currentPassword', { message: 'Current password is incorrect' });
        } else {
          setApiError(error.message);
        }
      } else {
        setApiError('Failed to change password');
      }
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-slate-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Failed to load profile data</p>
          <Button onClick={() => router.push('/dashboard')} className="mt-4">
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-slate-200">
            <h1 className="text-2xl font-bold text-slate-900">Account Settings</h1>
            <p className="mt-1 text-sm text-slate-600">
              Manage your account information and security settings
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-slate-200">
            <nav className="flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('profile')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'profile'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Profile Information
              </button>
              <button
                onClick={() => setActiveTab('security')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'security'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                Security
              </button>
            </nav>
          </div>

          <div className="p-6">
            {successMessage && (
              <div className="mb-6 rounded-md bg-green-50 p-4">
                <div className="text-sm text-green-700">{successMessage}</div>
              </div>
            )}

            {apiError && (
              <div className="mb-6 rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-700">{apiError}</div>
              </div>
            )}

            {activeTab === 'profile' && (
              <form onSubmit={profileForm.handleSubmit(onUpdateProfile)} className="space-y-6">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Personal Information</h3>
                    
                    <div className="space-y-4">
                      <FormInput
                        {...profileForm.register('firstName')}
                        label="First Name"
                        error={profileForm.formState.errors.firstName?.message}
                      />

                      <FormInput
                        {...profileForm.register('lastName')}
                        label="Last Name"
                        error={profileForm.formState.errors.lastName?.message}
                      />

                      <FormInput
                        {...profileForm.register('phoneNumber')}
                        label="Phone Number"
                        type="tel"
                        error={profileForm.formState.errors.phoneNumber?.message}
                        helperText="Optional"
                      />

                      <Select
                        {...profileForm.register('country')}
                        label="Country"
                        options={countries}
                        error={profileForm.formState.errors.country?.message}
                      />
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Account Information</h3>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-slate-700">Email</label>
                        <div className="mt-1 text-sm text-slate-900 bg-slate-50 px-3 py-2 rounded-md">
                          {user.email}
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          Contact support to change your email address
                        </p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-slate-700">Username</label>
                        <div className="mt-1 text-sm text-slate-900 bg-slate-50 px-3 py-2 rounded-md">
                          {user.username}
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          Username cannot be changed
                        </p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-slate-700">KYC Status</label>
                        <div className="mt-1">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.kyc_status === 'approved' 
                              ? 'bg-green-100 text-green-800'
                              : user.kyc_status === 'pending'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {user.kyc_status.charAt(0).toUpperCase() + user.kyc_status.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    loading={isUpdating}
                    disabled={isUpdating}
                  >
                    {isUpdating ? 'Updating...' : 'Update Profile'}
                  </Button>
                </div>
              </form>
            )}

            {activeTab === 'security' && (
              <div className="space-y-8">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Change Password</h3>
                  
                  <form onSubmit={passwordForm.handleSubmit(onChangePassword)} className="space-y-4 max-w-md">
                    <FormInput
                      {...passwordForm.register('currentPassword')}
                      type="password"
                      label="Current Password"
                      error={passwordForm.formState.errors.currentPassword?.message}
                      autoComplete="current-password"
                    />

                    <FormInput
                      {...passwordForm.register('newPassword')}
                      type="password"
                      label="New Password"
                      error={passwordForm.formState.errors.newPassword?.message}
                      autoComplete="new-password"
                      helperText="At least 8 characters with uppercase, lowercase, and number"
                    />

                    <FormInput
                      {...passwordForm.register('confirmNewPassword')}
                      type="password"
                      label="Confirm New Password"
                      error={passwordForm.formState.errors.confirmNewPassword?.message}
                      autoComplete="new-password"
                    />

                    <Button
                      type="submit"
                      loading={isChangingPassword}
                      disabled={isChangingPassword}
                    >
                      {isChangingPassword ? 'Changing Password...' : 'Change Password'}
                    </Button>
                  </form>
                </div>

                <div className="border-t border-slate-200 pt-8">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Two-Factor Authentication</h3>
                  
                  <div className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">
                        Two-Factor Authentication
                      </p>
                      <p className="text-sm text-slate-600">
                        {user.two_factor_enabled 
                          ? 'Your account is protected with 2FA'
                          : 'Add an extra layer of security to your account'
                        }
                      </p>
                    </div>
                    
                    <Button
                      variant={user.two_factor_enabled ? 'destructive' : 'default'}
                      onClick={() => router.push('/profile/2fa')}
                    >
                      {user.two_factor_enabled ? 'Disable 2FA' : 'Enable 2FA'}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}