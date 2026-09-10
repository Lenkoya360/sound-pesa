import Cookies from 'js-cookie';
import { AuthTokens, User } from '@sound-pesa/shared/types/user';
import { config } from './config';

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_data';

export class AuthManager {
  private static instance: AuthManager;
  private refreshTimer: NodeJS.Timeout | null = null;

  static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager();
    }
    return AuthManager.instance;
  }

  setTokens(tokens: AuthTokens): void {
    // Set access token with shorter expiry
    Cookies.set(TOKEN_KEY, tokens.access_token, {
      expires: new Date(Date.now() + tokens.expires_in * 1000),
      secure: config.NODE_ENV === 'production',
      sameSite: 'strict'
    });

    // Set refresh token with longer expiry (7 days)
    Cookies.set(REFRESH_TOKEN_KEY, tokens.refresh_token, {
      expires: 7,
      secure: config.NODE_ENV === 'production',
      sameSite: 'strict'
    });

    // Schedule automatic token refresh
    this.scheduleTokenRefresh(tokens.expires_in);
  }

  getAccessToken(): string | null {
    return Cookies.get(TOKEN_KEY) || null;
  }

  getRefreshToken(): string | null {
    return Cookies.get(REFRESH_TOKEN_KEY) || null;
  }

  setUser(user: User): void {
    Cookies.set(USER_KEY, JSON.stringify(user), {
      expires: 7,
      secure: config.NODE_ENV === 'production',
      sameSite: 'strict'
    });
  }

  getUser(): User | null {
    const userData = Cookies.get(USER_KEY);
    if (!userData) return null;
    
    try {
      return JSON.parse(userData);
    } catch {
      return null;
    }
  }

  clearAuth(): void {
    Cookies.remove(TOKEN_KEY);
    Cookies.remove(REFRESH_TOKEN_KEY);
    Cookies.remove(USER_KEY);
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  private scheduleTokenRefresh(expiresIn: number): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    // Refresh token 5 minutes before expiry
    const refreshTime = Math.max(0, (expiresIn - 300) * 1000);
    
    this.refreshTimer = setTimeout(async () => {
      await this.refreshAccessToken();
    }, refreshTime);
  }

  private async refreshAccessToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.clearAuth();
      return false;
    }

    try {
      const response = await fetch(`${config.NEXT_PUBLIC_API_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const tokens: AuthTokens = await response.json();
      this.setTokens(tokens);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearAuth();
      return false;
    }
  }

  async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getAccessToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // If token expired, try to refresh and retry
    if (response.status === 401 && token) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        const newToken = this.getAccessToken();
        if (newToken) {
          headers['Authorization'] = `Bearer ${newToken}`;
          return fetch(url, { ...options, headers });
        }
      }
    }

    return response;
  }
}

export const authManager = AuthManager.getInstance();