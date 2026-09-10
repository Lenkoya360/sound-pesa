import { randomBytes, createHash, createCipher, createDecipher, pbkdf2Sync, scryptSync } from 'crypto';
import { BlockchainNetwork } from '../types/blockchain';

/**
 * Generate a cryptographically secure random string
 */
export function generateSecureRandomString(length: number = 32): string {
  return randomBytes(length).toString('hex');
}

/**
 * Generate a secure private key for blockchain wallets
 */
export function generatePrivateKey(): string {
  return randomBytes(32).toString('hex');
}

/**
 * Create SHA256 hash of input data
 */
export function sha256Hash(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}

/**
 * Create a correlation ID for transaction tracking
 */
export function generateCorrelationId(): string {
  const timestamp = Date.now().toString(36);
  const random = generateSecureRandomString(8);
  return `${timestamp}-${random}`;
}

/**
 * Validate private key format (64 character hex string)
 */
export function isValidPrivateKey(privateKey: string): boolean {
  const privateKeyRegex = /^[a-fA-F0-9]{64}$/;
  return privateKeyRegex.test(privateKey);
}

/**
 * Generate a secure seed phrase (simplified - in production use proper BIP39)
 */
export function generateSeedPhrase(): string[] {
  // This is a simplified implementation
  // In production, use proper BIP39 mnemonic generation
  const words = [
    'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
    'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
    'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual'
  ];
  
  const seedPhrase: string[] = [];
  for (let i = 0; i < 12; i++) {
    const randomIndex = Math.floor(Math.random() * words.length);
    const word = words[randomIndex];
    if (word) {
      seedPhrase.push(word);
    }
  }
  
  return seedPhrase;
}

/**
 * Enhanced private key generation for specific blockchains
 */
export function generatePrivateKeyForBlockchain(blockchain: BlockchainNetwork): string {
  switch (blockchain) {
    case 'bitcoin':
    case 'ethereum':
      // Standard 32-byte private key
      return randomBytes(32).toString('hex');
    case 'cardano':
      // Cardano uses extended private keys, but simplified here
      return randomBytes(32).toString('hex');
    case 'polkadot':
      // Polkadot uses sr25519 keys, but simplified here
      return randomBytes(32).toString('hex');
    default:
      return randomBytes(32).toString('hex');
  }
}

/**
 * Encrypt private key using AES-256-GCM
 */
export function encryptPrivateKey(privateKey: string, password: string): string {
  try {
    const salt = randomBytes(16);
    const iv = randomBytes(12);
    const key = scryptSync(password, salt, 32);
    
    const cipher = createCipher('aes-256-gcm', key);
    let encrypted = cipher.update(privateKey, 'hex', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    // Combine salt, iv, authTag, and encrypted data
    const combined = Buffer.concat([salt, iv, authTag, Buffer.from(encrypted, 'hex')]);
    return combined.toString('base64');
  } catch (error) {
    throw new Error('Failed to encrypt private key');
  }
}

/**
 * Decrypt private key using AES-256-GCM
 */
export function decryptPrivateKey(encryptedPrivateKey: string, password: string): string {
  try {
    const combined = Buffer.from(encryptedPrivateKey, 'base64');
    
    const salt = combined.slice(0, 16);
    // const iv = combined.slice(16, 28); // IV not needed for decryption with GCM
    const authTag = combined.slice(28, 44);
    const encrypted = combined.slice(44);
    
    const key = scryptSync(password, salt, 32);
    
    const decipher = createDecipher('aes-256-gcm', key);
    decipher.setAuthTag(authTag);
    
    let decrypted = decipher.update(encrypted, undefined, 'hex');
    decrypted += decipher.final('hex');
    
    return decrypted;
  } catch (error) {
    throw new Error('Failed to decrypt private key');
  }
}

/**
 * Generate a secure wallet seed
 */
export function generateWalletSeed(): Buffer {
  return randomBytes(64); // 512-bit seed
}

/**
 * Derive key from password using PBKDF2
 */
export function deriveKeyFromPassword(password: string, salt: string, iterations: number = 100000): Buffer {
  return pbkdf2Sync(password, salt, iterations, 32, 'sha256');
}

/**
 * Generate secure salt for key derivation
 */
export function generateSalt(): string {
  return randomBytes(16).toString('hex');
}

/**
 * Create HMAC signature
 */
export function createHMACSignature(data: string, secret: string): string {
  const hmac = createHash('sha256');
  hmac.update(data + secret);
  return hmac.digest('hex');
}

/**
 * Verify HMAC signature
 */
export function verifyHMACSignature(data: string, signature: string, secret: string): boolean {
  const expectedSignature = createHMACSignature(data, secret);
  return signature === expectedSignature;
}

/**
 * Generate blockchain-specific address from private key (simplified)
 * Note: In production, use proper blockchain libraries
 */
export function generateAddressFromPrivateKey(privateKey: string, blockchain: BlockchainNetwork): string {
  const hash = sha256Hash(privateKey + blockchain);
  
  switch (blockchain) {
    case 'bitcoin':
      return '1' + hash.substring(0, 33); // Simplified Bitcoin address
    case 'ethereum':
      return '0x' + hash.substring(0, 40); // Simplified Ethereum address
    case 'cardano':
      return 'addr1' + hash.substring(0, 58); // Simplified Cardano address
    case 'polkadot':
      return '1' + hash.substring(0, 47); // Simplified Polkadot address
    default:
      throw new Error(`Unsupported blockchain: ${blockchain}`);
  }
}

/**
 * Generate secure API key
 */
export function generateAPIKey(): string {
  return 'sk_' + generateSecureRandomString(32);
}

/**
 * Generate secure session token
 */
export function generateSessionToken(): string {
  return generateSecureRandomString(48);
}

/**
 * Hash password using scrypt
 */
export function hashPassword(password: string, salt?: string): { hash: string; salt: string } {
  const passwordSalt = salt || generateSalt();
  const hash = scryptSync(password, passwordSalt, 64).toString('hex');
  return { hash, salt: passwordSalt };
}

/**
 * Verify password against hash
 */
export function verifyPassword(password: string, hash: string, salt: string): boolean {
  const { hash: computedHash } = hashPassword(password, salt);
  return computedHash === hash;
}