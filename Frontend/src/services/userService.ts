import { User } from '../models/user';
import { API_BASE_URL } from '../config';
import { authService } from './authService';

export const userService = {

    getUserId: (): number | null => {
        const userId = localStorage.getItem('user_id');
        console.log(userId);
        return userId ? parseInt(userId) : null;
    },

    getCurrentUser: async (reload?: boolean): Promise<User> => {
        // If livereload is true, clear the cache, so we get the newest data
        if (reload) {
            localStorage.removeItem('user_data');
        }

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
            const userData = await userService.getCurrentUser();
            return userData.is_admin;
        } catch (error) {
            console.error('Error checking admin status:', error);
            return false;
        }
    },

    updateCurrentUsersUsername: async (newUsername: string): Promise<User> => {
        const userId = userService.getUserId();
        console.log(userId);
        if (!userId) {
            throw new Error('User ID not found');
        }

        const token = authService.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE_URL}/user/${userId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: newUsername
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update username');
        }

        const updatedUser = await response.json();

        // Update the cached user data
        localStorage.setItem('user_data', JSON.stringify(updatedUser));

        return updatedUser;
    },

    // Helper method to clear cached user data (useful after profile updates)
    clearUserCache: () => {
        localStorage.removeItem('user_data');
    }
};
