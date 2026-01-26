import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Word {
  id: number;
  text: string;
  price: string;
  owner_name: string | null;
  owner_message: string | null;
  lockout_ends_at: string | null;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface WordDetail extends Word {
  transaction_count: number;
  transactions: Transaction[];
}

export interface Transaction {
  id: number;
  buyer_name: string;
  price_paid: string;
  timestamp: string;
}

export interface SearchResponse {
  words: Word[];
  total: number;
  page: number;
  page_size: number;
}

export interface PlatformStats {
  total_words: number;
  words_owned: number;
  words_available: number;
  total_transactions: number;
  total_revenue: number;
  average_price: number;
}

// API Methods
export const wordApi = {
  search: async (query?: string, status?: string, page: number = 1) => {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (status) params.append('status', status);
    params.append('page', page.toString());

    const response = await api.get<SearchResponse>(`/api/words/search?${params}`);
    return response.data;
  },

  getRandom: async () => {
    const response = await api.get<Word>('/api/words/random');
    return response.data;
  },

  getWord: async (word: string) => {
    const response = await api.get<WordDetail>(`/api/words/${word}`);
    return response.data;
  },

  purchase: async (word: string, ownerName: string, ownerMessage: string) => {
    const response = await api.post(`/api/purchase/${word}`, {
      owner_name: ownerName,
      owner_message: ownerMessage,
    });
    return response.data;
  },

  addWord: async (word: string, ownerName: string, ownerMessage: string) => {
    const response = await api.post(`/api/purchase/add/${word}`, {
      owner_name: ownerName,
      owner_message: ownerMessage,
    });
    return response.data;
  },
};

export const leaderboardApi = {
  getMostExpensive: async (limit: number = 10) => {
    const response = await api.get<Word[]>(`/api/leaderboard/expensive?limit=${limit}`);
    return response.data;
  },

  getRecent: async (limit: number = 10) => {
    const response = await api.get<Transaction[]>(`/api/leaderboard/recent?limit=${limit}`);
    return response.data;
  },

  getStats: async () => {
    const response = await api.get<PlatformStats>('/api/leaderboard/stats');
    return response.data;
  },
};
