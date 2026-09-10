// API response types
export interface APIResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
  timestamp: Date;
}