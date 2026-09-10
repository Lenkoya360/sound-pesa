import { authManager } from './auth';
import { config } from './config';
import { LoginCredentials, RegisterData, AuthTokens, User } from '@sound-pesa/shared/types/user';
import { 
  Wallet, 
  WalletBalance, 
  BlockchainNetwork, 
  BlockchainStatus 
} from '@sound-pesa/shared/types/blockchain';
import { 
  Transaction, 
  TransactionEstimate, 
  TransactionSendRequest, 
  TransactionHistory 
} from '@sound-pesa/shared/types/transaction';

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class APIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = config.NEXT_PUBLIC_API_URL;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }

      throw new APIError(
        errorData.error?.message || `HTTP ${response.status}`,
        response.status,
        errorData.error?.code,
        errorData.error?.details
      );
    }

    return response.json();
  }

  async login(credentials: LoginCredentials): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    return this.handleResponse(response);
  }

  async register(data: RegisterData): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await fetch(`${this.baseURL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  async logout(): Promise<void> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/auth/logout`,
      { method: 'POST' }
    );

    if (!response.ok) {
      // Even if logout fails on server, clear local tokens
      console.warn('Server logout failed, clearing local tokens');
    }
    
    authManager.clearAuth();
  }

  async getUserProfile(): Promise<User> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/user/profile`
    );

    return this.handleResponse(response);
  }

  async updateUserProfile(data: Partial<User>): Promise<User> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/user/profile`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      }
    );

    return this.handleResponse(response);
  }

  async enable2FA(): Promise<{ qr_code: string; secret: string }> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/auth/2fa/enable`,
      { method: 'POST' }
    );

    return this.handleResponse(response);
  }

  async verify2FA(code: string): Promise<{ backup_codes: string[] }> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/auth/2fa/verify`,
      {
        method: 'POST',
        body: JSON.stringify({ code }),
      }
    );

    return this.handleResponse(response);
  }

  async disable2FA(code: string): Promise<void> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/auth/2fa/disable`,
      {
        method: 'POST',
        body: JSON.stringify({ code }),
      }
    );

    return this.handleResponse(response);
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/auth/change-password`,
      {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      }
    );

    return this.handleResponse(response);
  }

  // Wallet Management
  async getWallets(): Promise<Wallet[]> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/wallets`
    );

    return this.handleResponse(response);
  }

  async createWallet(blockchain: BlockchainNetwork): Promise<Wallet> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/wallets/create`,
      {
        method: 'POST',
        body: JSON.stringify({ blockchain }),
      }
    );

    return this.handleResponse(response);
  }

  async getWalletBalance(blockchain: BlockchainNetwork): Promise<WalletBalance> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/wallets/${blockchain}/balance`
    );

    return this.handleResponse(response);
  }

  async getWalletHistory(blockchain: BlockchainNetwork, page = 1, pageSize = 20): Promise<TransactionHistory> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/wallets/${blockchain}/history?page=${page}&page_size=${pageSize}`
    );

    return this.handleResponse(response);
  }

  // Transaction Management
  async sendTransaction(request: TransactionSendRequest): Promise<Transaction> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/transactions/send`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return this.handleResponse(response);
  }

  async getTransaction(id: string): Promise<Transaction> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/transactions/${id}`
    );

    return this.handleResponse(response);
  }

  async getPendingTransactions(): Promise<Transaction[]> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/transactions/pending`
    );

    return this.handleResponse(response);
  }

  async estimateTransactionFee(
    blockchain: BlockchainNetwork,
    amount: string,
    toAddress: string
  ): Promise<TransactionEstimate> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/transactions/estimate-fee`,
      {
        method: 'POST',
        body: JSON.stringify({
          blockchain,
          amount,
          to_address: toAddress,
        }),
      }
    );

    return this.handleResponse(response);
  }

  // Blockchain Status
  async getBlockchainStatus(blockchain: BlockchainNetwork): Promise<BlockchainStatus> {
    const response = await authManager.makeAuthenticatedRequest(
      `${this.baseURL}/api/blockchain/${blockchain}/status`
    );

    return this.handleResponse(response);
  }
}

export const apiClient = new APIClient();