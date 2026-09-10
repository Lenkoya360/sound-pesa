// Validation utilities
import { z } from 'zod';
import { BlockchainNetwork } from '../types';

export const emailSchema = z.string().email('Invalid email address');

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters');

export function validateAddress(address: string, blockchain: BlockchainNetwork): boolean {
  // Basic validation - would be more sophisticated in real implementation
  return address.length > 10;
}