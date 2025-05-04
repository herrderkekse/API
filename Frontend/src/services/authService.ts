import { API_BASE_URL } from '../config';
import { userService } from './userService';


export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: number;
}

export const authService = {
  login: async (username: string, password: string): Promise<void> => {
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

    console.log(data);
    return data;
  },

  loginWithKeycard: async (keyCardId: string, pin: string): Promise<void> => {
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

  removeCurrentUsersKeycard: async (): Promise<void> => {
    const userId = userService.getUserId();
    const token = authService.getToken();
    if (!userId || !token) {
      throw new Error('Not authenticated');
    }
    const response = await fetch(`${API_BASE_URL}/user/${userId}/keycard`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to remove keycard');
    }
  },
};
