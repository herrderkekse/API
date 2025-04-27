import { useState } from 'react';
import { Button } from '../Button/Button';
import { LoadingSpinner } from '../LoadingSpinner/LoadingSpinner';
import './DeviceCard.css';

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

interface DeviceCardProps {
  device: Device;
  onStopDevice: (id: number) => Promise<void>;
  currentUser: User;
  users: User[];
}

const formatTimeLeft = (seconds: number): string => {
  if (seconds <= 0) return 'Not running';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  parts.push(`${remainingSeconds}s`);

  return parts.join(' ');
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

export const DeviceCard = ({ device, onStopDevice, currentUser, users }: DeviceCardProps) => {
  const [isStopping, setIsStopping] = useState(false);

  const isRunning = device.time_left && device.time_left > 0;
  const isAdmin = currentUser.is_admin;
  const deviceUser = users.find(u => u.uid === device.user_id);
  const canStop = isAdmin || currentUser.uid === device.user_id;

  const handleStopDevice = async () => {
    try {
      setIsStopping(true);
      await onStopDevice(device.id);
    } finally {
      setIsStopping(false);
    }
  };

  const renderRunningInfo = () => {
    if (!isRunning) return null;

    return (
      <>
        <div className="info-row">
          <span className="label">Time Left</span>
          <span>{formatTimeLeft(device.time_left || 0)}</span>
        </div>

        <div className="info-row">
          <span className="label">End Time</span>
          <span>
            {device.end_time ? new Date(device.end_time).toLocaleString() : 'N/A'}
          </span>
        </div>

        <div className="info-row">
          <span className="label">User</span>
          <span>{deviceUser ? deviceUser.name : `ID: ${device.user_id}`}</span>
        </div>

        {canStop && (
          <Button
            variant="danger"
            fullWidth
            onClick={handleStopDevice}
            disabled={isStopping}
          >
            {isStopping ? (
              <div className="button-content">
                <LoadingSpinner size={16} color="white" />
                <span className="ml-2">Stopping...</span>
              </div>
            ) : (
              'Stop Device'
            )}
          </Button>
        )}
      </>
    );
  };

  return (
    <div className="device-card">
      <div className="device-header">
        <h3>
          {device.name}
          <span className="device-type">{device.type}</span>
        </h3>
      </div>

      <div className="device-info">
        <div className="info-row">
          <span className="label">Status</span>
          <span className={isRunning ? 'status-running' : 'status-available'}>
            {isRunning ? 'Running' : 'Available'}
          </span>
        </div>

        <div className="info-row">
          <span className="label">Cost</span>
          <span>{formatCurrency(device.hourly_cost)}/hour</span>
        </div>

        {renderRunningInfo()}
      </div>
    </div>
  );
};
