/**
 * Admin API client functions.
 * All requests require X-Admin-Token header with 6-digit TOTP code.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface IncomeStats {
  total_income: number;
  today_income: number;
  week_income: number;
  total_transactions: number;
  today_transactions: number;
  week_transactions: number;
}

export interface PopularWord {
  word: string;
  price: number;
  owner: string | null;
  views: number;
}

export interface ErrorLog {
  id: number;
  type: string;
  message: string;
  stack_trace: string | null;
  endpoint: string | null;
  user_info: string | null;
  timestamp: string;
}

export interface DashboardData {
  income: IncomeStats;
  popular_words: PopularWord[];
  recent_errors: ErrorLog[];
  stats: {
    total_words: number;
    available_words: number;
    locked_words: number;
  };
}

export interface SetupInfo {
  secret: string;
  qr_code: string;
  manual_entry: string;
  instructions: string;
}

export interface ResetWordData {
  word: string;
  new_price: number;
  owner_name?: string;
  owner_message?: string;
}

export interface ReportedMessage {
  word_id: number;
  word_text: string;
  owner_name: string | null;
  owner_message: string | null;
  report_count: number;
  moderation_status: string | null;
  moderated_at: string | null;
  updated_at: string;
  lockout_ends_at: string | null;
}

export interface ReportedMessagesResponse {
  messages: ReportedMessage[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Store/retrieve admin token in session storage.
 */
export const adminTokenStorage = {
  set: (token: string) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('admin_token', token);
    }
  },
  get: (): string | null => {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('admin_token');
    }
    return null;
  },
  clear: () => {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('admin_token');
    }
  }
};

/**
 * Make authenticated admin API request.
 */
async function adminRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = adminTokenStorage.get();

  if (!token) {
    throw new Error('Admin token required. Please log in.');
  }

  const headers = {
    'Content-Type': 'application/json',
    'X-Admin-Token': token,
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Verify admin TOTP code (login).
 */
export async function adminLogin(totpCode: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ totp_code: totpCode }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json();

  // Store token for subsequent requests
  adminTokenStorage.set(totpCode);

  return data;
}

/**
 * Get TOTP setup information (QR code).
 */
export async function getSetupInfo(): Promise<SetupInfo> {
  const response = await fetch(`${API_BASE_URL}/api/admin/setup`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get setup info');
  }

  return response.json();
}

/**
 * Get admin dashboard data.
 */
export async function getDashboard(): Promise<DashboardData> {
  return adminRequest<DashboardData>('/api/admin/dashboard');
}

/**
 * Get income statistics.
 */
export async function getIncomeStats(): Promise<IncomeStats> {
  return adminRequest<IncomeStats>('/api/admin/income');
}

/**
 * Get most popular words.
 */
export async function getPopularWords(limit: number = 20): Promise<PopularWord[]> {
  return adminRequest<PopularWord[]>(`/api/admin/popular-words?limit=${limit}`);
}

/**
 * Get recent errors.
 */
export async function getRecentErrors(limit: number = 50): Promise<ErrorLog[]> {
  return adminRequest<ErrorLog[]>(`/api/admin/errors?limit=${limit}`);
}

/**
 * Reset a word's price and ownership.
 */
export async function resetWord(data: ResetWordData): Promise<any> {
  return adminRequest('/api/admin/reset-word', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get reported messages with pagination.
 */
export async function getReportedMessages(page: number = 1, pageSize: number = 20): Promise<ReportedMessagesResponse> {
  return adminRequest<ReportedMessagesResponse>(`/api/admin/reported-messages?page=${page}&page_size=${pageSize}`);
}

/**
 * Moderate a reported message (approve, reject, or protect).
 */
export async function moderateMessage(wordId: number, action: 'approve' | 'reject' | 'protect'): Promise<any> {
  return adminRequest('/api/admin/moderate-message', {
    method: 'POST',
    body: JSON.stringify({ word_id: wordId, action }),
  });
}

/**
 * Logout (clear stored token).
 */
export function adminLogout() {
  adminTokenStorage.clear();
}
