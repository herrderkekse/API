import { API_BASE_URL } from '../config';

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: number;
}

export interface UserData {
  uid: number;
  name: string;
  cash: number;
  creation_time: string;
  is_admin: boolean;
  has_keycard: boolean;
}

export const authService = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user_id', data.user_id.toString());
    return data;
  },

  loginWithKeycard: async (keyCardId: string, pin: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/token/keycard`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        key_card_id: keyCardId,
        pin: pin
      }),
    });

    if (!response.ok) {
      throw new Error('Keycard login failed');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user_id', data.user_id.toString());
    return data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    // Clear any cached user data
    localStorage.removeItem('user_data');
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('token');
  },

  getToken: (): string | null => {
    return localStorage.getItem('token');
  },

  getUserId: (): number | null => {
    const userId = localStorage.getItem('user_id');
    return userId ? parseInt(userId) : null;
  },

  getCurrentUser: async (): Promise<UserData> => {
    // Check if we have cached user data
    const cachedData = localStorage.getItem('user_data');
    if (cachedData) {
      return JSON.parse(cachedData);
    }

    const token = authService.getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user data');
    }

    const userData = await response.json();
    // Cache the user data
    localStorage.setItem('user_data', JSON.stringify(userData));
    return userData;
  },

  isAdmin: async (): Promise<boolean> => {
    try {
      const userData = await authService.getCurrentUser();
      return userData.is_admin;
    } catch (error) {
      console.error('Error checking admin status:', error);
      return false;
    }
  },

  // Helper method to clear cached user data (useful after profile updates)
  clearUserCache: () => {
    localStorage.removeItem('user_data');
  }
};
