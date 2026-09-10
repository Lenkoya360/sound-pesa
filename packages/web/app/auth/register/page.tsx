'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FormInput } from '@/components/ui/form-input';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { registerSchema, RegisterFormData } from '@/lib/validations';
import { apiClient, APIError } from '@/lib/api';
import { authManager } from '@/lib/auth';

// Common countries list
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

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const response = await apiClient.register({
        email: data.email,
        username: data.username,
        password: data.password,
        first_name: data.firstName,
        last_name: data.lastName,
        country: data.country,
      });

      // Store tokens and user data
      authManager.setTokens(response.tokens);
      authManager.setUser(response.user);

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      if (error instanceof APIError) {
        if (error.code === 'VALIDATION_EMAIL_EXISTS') {
          setError('email', { message: 'This email is already registered' });
        } else if (error.code === 'VALIDATION_USERNAME_EXISTS') {
          setError('username', { message: 'This username is already taken' });
        } else if (error.details) {
          // Handle field-specific validation errors
          Object.entries(error.details).forEach(([field, messages]) => {
            if (Array.isArray(messages) && messages.length > 0) {
              setError(field as keyof RegisterFormData, { message: messages[0] });
            }
          });
        } else {
          setApiError(error.message);
        }
      } else {
        setApiError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="h-12 w-12 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-xl">S</span>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-slate-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600">
            Already have an account?{' '}
            <Link
              href="/auth/login"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              Sign in
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {apiError && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{apiError}</div>
            </div>
          )}

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormInput
                {...register('firstName')}
                type="text"
                label="First name"
                placeholder="John"
                error={errors.firstName?.message}
                autoComplete="given-name"
              />

              <FormInput
                {...register('lastName')}
                type="text"
                label="Last name"
                placeholder="Doe"
                error={errors.lastName?.message}
                autoComplete="family-name"
              />
            </div>

            <FormInput
              {...register('email')}
              type="email"
              label="Email address"
              placeholder="john@example.com"
              error={errors.email?.message}
              autoComplete="email"
            />

            <FormInput
              {...register('username')}
              type="text"
              label="Username"
              placeholder="johndoe"
              error={errors.username?.message}
              autoComplete="username"
              helperText="3-30 characters, letters, numbers, hyphens, and underscores only"
            />

            <Select
              {...register('country')}
              label="Country"
              options={countries}
              error={errors.country?.message}
            />

            <FormInput
              {...register('password')}
              type="password"
              label="Password"
              placeholder="Create a strong password"
              error={errors.password?.message}
              autoComplete="new-password"
              helperText="At least 8 characters with uppercase, lowercase, and number"
            />

            <FormInput
              {...register('confirmPassword')}
              type="password"
              label="Confirm password"
              placeholder="Confirm your password"
              error={errors.confirmPassword?.message}
              autoComplete="new-password"
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            loading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </Button>
        </form>

        <div className="text-center text-xs text-slate-500">
          By creating an account, you agree to our{' '}
          <Link href="/terms" className="text-blue-600 hover:text-blue-500">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
            Privacy Policy
          </Link>
        </div>
      </div>
    </div>
  );
}