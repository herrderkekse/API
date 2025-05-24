import { useState } from 'react';
import { Button } from '../Button/Button';
import { LoadingSpinner } from '../LoadingSpinner/LoadingSpinner';
import './DeviceCard.css';
import { User } from '../../models/user';

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
  onStartDevice: (id: number, duration: number) => Promise<void>;
}



export const DeviceCard = ({ device, onStopDevice, onStartDevice, currentUser, users }: DeviceCardProps) => {
  const [isStopping, setIsStopping] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(30);
  const [isExpanded, setIsExpanded] = useState(false);

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

  const handleStartDevice = async () => {
    try {
      setIsStarting(true);
      const totalMinutes = (hours * 60) + minutes;
      await onStartDevice(device.id, totalMinutes);
      setIsExpanded(false);
    } finally {
      setIsStarting(false);
    }
  };

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

  const formatCurrency = (amount: number) => {
    return `€${amount.toFixed(2)}`;
  };

  const calculateCost = (): string => {
    const totalMinutes = (hours * 60) + minutes;
    const cost = (device.hourly_cost * totalMinutes) / 60;
    return formatCurrency(cost);
  };

  return (
    <div
      className={`device-card ${isRunning ? 'running' : ''} ${isExpanded ? 'expanded' : ''}`}
      onClick={() => !isRunning && setIsExpanded(!isExpanded)}
    >
      <div className="device-header">
        <div className="device-title">
          <h3>{device.name}</h3>
          <span className="device-type">{device.type}</span>
        </div>
        <div className="device-status">
          <span className={`status-indicator ${isRunning ? 'running' : 'available'}`}>
            {isStarting || isStopping ? (
              <>
                <LoadingSpinner size={14} color={isRunning ? '#2E7D32' : '#1976D2'} />
                <span>{isStarting ? 'Starting...' : 'Stopping...'}</span>
              </>
            ) : (
              isRunning ? 'In Use' : 'Available'
            )}
          </span>
        </div>
      </div>

      {isRunning ? (
        <div className="device-content">
          <div className="info-grid">
            <div className="info-item">
              <span className="label">Time Left</span>
              <span className="value">{formatTimeLeft(device.time_left || 0)}</span>
            </div>
            <div className="info-item">
              <span className="label">User</span>
              <span className="value">{deviceUser ? deviceUser.name : `ID: ${device.user_id}`}</span>
            </div>
          </div>

          {canStop && (
            <div className="action-buttons">
              <Button
                variant="danger"
                fullWidth
                onClick={(e) => {
                  e.stopPropagation();
                  handleStopDevice();
                }}
                disabled={isStopping}
              >
                {isStopping ? (
                  <>
                    <LoadingSpinner size={16} color="white" />
                    <span>Stopping...</span>
                  </>
                ) : (
                  'Stop Device'
                )}
              </Button>
            </div>
          )}
        </div>
      ) : (
        <div className={`device-content ${isExpanded ? 'show' : ''}`}>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">Cost</span>
              <span className="value">{formatCurrency(device.hourly_cost)}/hour</span>
            </div>
          </div>

          {isExpanded && (
            <div className="start-controls" onClick={e => e.stopPropagation()}>
              <div className="duration-selector">
                <label>Duration:</label>
                <div className="time-inputs">
                  <div className="time-input-group">
                    <input
                      type="number"
                      min="0"
                      max="24"
                      value={hours}
                      onChange={(e) => setHours(Math.min(24, Math.max(0, parseInt(e.target.value) || 0)))}
                      className="time-input"
                    />
                    <span className="time-label">hours</span>
                  </div>
                  <div className="time-input-group">
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={minutes}
                      onChange={(e) => setMinutes(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
                      className="time-input"
                    />
                    <span className="time-label">minutes</span>
                  </div>
                </div>
                <div className="estimated-cost">
                  Estimated cost: {calculateCost()}
                </div>
              </div>

              <div className="quick-duration-buttons">
                <Button
                  variant="ghost"
                  onClick={() => { setHours(0); setMinutes(30); }}
                >
                  30m
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => { setHours(1); setMinutes(0); }}
                >
                  1h
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => { setHours(1); setMinutes(30); }}
                >
                  1.5h
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => { setHours(2); setMinutes(0); }}
                >
                  2h
                </Button>
              </div>

              <div className="action-buttons">
                <Button
                  variant="primary"
                  fullWidth
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStartDevice();
                  }}
                  disabled={isStarting || (hours === 0 && minutes === 0)}
                >
                  {isStarting ? (
                    <>
                      <LoadingSpinner size={16} color="white" />
                      <span>Starting...</span>
                    </>
                  ) : (
                    'Start Device'
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
