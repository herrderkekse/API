import { useEffect, useState } from 'react';
import './DeviceScreen.css';
import { DeviceCard } from '../DeviceCard/DeviceCard';
import { API_BASE_URL } from '../../config';

interface User {
  uid: number;
  name: string;
  cash: number;
  is_admin: boolean;
  creation_time: string;
}

interface Device {
  id: number;
  name: string;
  type: string;
  hourly_cost: number;
  user_id: number | null;
  end_time: string | null;
  time_left: number | null;
}

export function DeviceScreen() {
  const [users, setUsers] = useState<User[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deviceWebsockets, setDeviceWebsockets] = useState<{ [key: number]: WebSocket }>({});
  const WS_URL = 'ws://localhost:8000';
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadUsers();
    loadDevices();

    return () => {
      // Cleanup WebSocket connections on component unmount
      Object.values(deviceWebsockets).forEach(ws => ws.close());
    };
  }, []);

  const loadUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/user/all`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to load users');
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Error loading users:', error);
      setError(error instanceof Error ? error.message : 'Failed to load users');
    }
  };

  const loadDevices = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/device/all`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to load devices');
      const data = await response.json();
      setDevices(data);
      initializeDeviceWebsockets(data);
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  };

  const initializeDeviceWebsockets = (devices: Device[]) => {
    // Close existing connections
    Object.values(deviceWebsockets).forEach(ws => ws.close());
    const newWebsockets: { [key: number]: WebSocket } = {};

    devices.forEach(device => {
      const ws = new WebSocket(`${WS_URL}/device/ws/timeleft/${device.id}`);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setDevices(prevDevices =>
          prevDevices.map(d => {
            if (d.id === data.device_id) {
              return {
                ...d,
                user_id: data.user_id,
                time_left: data.time_left
              };
            }
            return d;
          })
        );
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error for device ${device.id}:`, error);
      };

      ws.onclose = () => {
        console.log(`WebSocket closed for device ${device.id}`);
      };

      newWebsockets[device.id] = ws;
    });

    setDeviceWebsockets(newWebsockets);
  };

  const handleStopDevice = async (deviceId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/device/stop/${deviceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to stop device');
    } catch (error) {
      console.error('Error stopping device:', error);
      throw error;
    }
  };

  const handleStartDevice = async (deviceId: number, duration: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/device/start/${deviceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: users.find(u => u.is_admin)?.uid || -1,
          duration_minutes: duration
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start device');
      }
    } catch (error) {
      console.error('Error starting device:', error);
      throw error;
    }
  };

  return (
    <div className="dashboard">
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      <div className="devices-section">
        <div className="device-grid">
          {devices.map(device => (
            <DeviceCard
              key={device.id}
              device={device}
              onStopDevice={handleStopDevice}
              onStartDevice={handleStartDevice}
              currentUser={users.find(u => u.is_admin) || { uid: 0, name: '', cash: 0, creation_time: new Date().toISOString(), is_admin: false }}
              users={users}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
