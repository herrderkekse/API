import { API_BASE_URL } from '../config';

export interface Device {
  id: number;
  name: string;
  type: string;
  hourly_cost: number;
  user_id: number | null;
  end_time: string | null;
  time_left: number | null;
}

export const deviceService = {
  getAllDevices: async (): Promise<Device[]> => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/device/all`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to load devices');
    }
    
    return await response.json();
  },
  
  stopDevice: async (deviceId: number): Promise<void> => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/device/stop/${deviceId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to stop device');
    }
  },
  
  startDevice: async (deviceId: number, userId: number, duration: number): Promise<void> => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/device/start/${deviceId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        duration_minutes: duration
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start device');
    }
  }
};