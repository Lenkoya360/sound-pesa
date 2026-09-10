/**
 * Environment configuration and validation
 */

export interface EnvironmentConfig {
  NODE_ENV: 'development' | 'production' | 'test';
  API_BASE_URL: string;
  WS_BASE_URL: string;
  DATABASE_URL: string;
  REDIS_URL: string;
  VAULT_URL: string;
  JWT_SECRET: string;
  CORS_ORIGINS: string[];
  LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error';
}

/**
 * Get environment configuration with defaults
 */
export function getEnvironmentConfig(): EnvironmentConfig {
  return {
    NODE_ENV: (process.env['NODE_ENV'] as any) || 'development',
    API_BASE_URL: process.env['API_BASE_URL'] || 'http://localhost:8000',
    WS_BASE_URL: process.env['WS_BASE_URL'] || 'ws://localhost:8000',
    DATABASE_URL: process.env['DATABASE_URL'] || 'postgresql://postgres:password@postgres:5432/soundpesa',
    REDIS_URL: process.env['REDIS_URL'] || 'redis://redis:6379',
    VAULT_URL: process.env['VAULT_URL'] || 'http://vault:8200',
    JWT_SECRET: process.env['JWT_SECRET'] || 'your-secret-key-change-in-production',
    CORS_ORIGINS: process.env['CORS_ORIGINS']?.split(',') || ['http://localhost:3000', 'http://localhost:3001'],
    LOG_LEVEL: (process.env['LOG_LEVEL'] as any) || 'info'
  };
}

/**
 * Validate required environment variables
 */
export function validateEnvironment(): void {
  const required = [
    'DATABASE_URL',
    'REDIS_URL',
    'JWT_SECRET'
  ];

  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
}

/**
 * Check if running in development mode
 */
export function isDevelopment(): boolean {
  return process.env['NODE_ENV'] === 'development';
}

/**
 * Check if running in production mode
 */
export function isProduction(): boolean {
  return process.env['NODE_ENV'] === 'production';
}

/**
 * Check if running in test mode
 */
export function isTest(): boolean {
  return process.env['NODE_ENV'] === 'test';
}