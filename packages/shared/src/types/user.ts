// User and authentication types
export interface User {
  id: string;
  email: string;
  username: string;
  created_at: Date;
  updated_at: Date;
  is_active: boolean;
  two_factor_enabled: boolean;
  kyc_status: KYCStatus;
}

export type KYCStatus = 'pending' | 'approved' | 'rejected' | 'not_started';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'Bearer';
}