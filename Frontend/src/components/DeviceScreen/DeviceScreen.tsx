import { useEffect, useState } from 'react';
import './DeviceScreen.css';
import { DeviceCard } from '../DeviceCard/DeviceCard';
import { deviceService, Device } from '../../services/deviceService';
import { userService } from '../../services/userService';
import { websocketService } from '../../services/websocketService';
import { User } from '../../models/user';

export function DeviceScreen() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deviceWebsockets, setDeviceWebsockets] = useState<{ [key: number]: WebSocket }>({});

  useEffect(() => {
    loadCurrentUser();
    loadDevices();

    return () => {
      // Cleanup WebSocket connections on component unmount
      Object.values(deviceWebsockets).forEach(ws => websocketService.closeWebSocket(ws));
    };
  }, []);

  const loadCurrentUser = async () => {
    try {
      const userData = await userService.getCurrentUser();
      setCurrentUser(userData);
    } catch (error) {
      console.error('Error loading current user:', error);
      setError(error instanceof Error ? error.message : 'Failed to load user');
    }
  };

  const loadDevices = async () => {
    try {
      const data = await deviceService.getAllDevices();
      setDevices(data);
      initializeDeviceWebsockets(data);
    } catch (error) {
      console.error('Error loading devices:', error);
      setError(error instanceof Error ? error.message : 'Failed to load devices');
    }
  };

  const initializeDeviceWebsockets = (devices: Device[]) => {
    // Close existing connections
    Object.values(deviceWebsockets).forEach(ws => websocketService.closeWebSocket(ws));
    const newWebsockets: { [key: number]: WebSocket } = {};

    devices.forEach(device => {
      const ws = websocketService.createDeviceTimeLeftSocket(device.id, (data) => {
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
      });

      newWebsockets[device.id] = ws;
    });

    setDeviceWebsockets(newWebsockets);
  };

  const handleStopDevice = async (deviceId: number) => {
    try {
      await deviceService.stopDevice(deviceId);
    } catch (error) {
      console.error('Error stopping device:', error);
      throw error;
    }
  };

  const handleStartDevice = async (deviceId: number, duration: number) => {
    try {
      if (!currentUser) {
        throw new Error('Admin privileges required');
      }
      await deviceService.startDevice(deviceId, currentUser.uid, duration);
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
              currentUser={currentUser || { uid: 0, name: '', cash: 0, creation_time: new Date().toISOString(), is_admin: false, has_keycard: false }}
              users={[]}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
