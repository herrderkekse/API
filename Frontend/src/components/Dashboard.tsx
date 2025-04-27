import { useEffect, useState } from 'react';
import './Dashboard.css';
import { Button } from './Button/Button';
import { DeviceCard } from './DeviceCard/DeviceCard';
import { UserTable } from './UserTable/UserTable';

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

interface CreateUserModal {
  isOpen: boolean;
  username: string;
  password: string;
  isAdmin: boolean;
}

interface EditUserModal {
  user: User | null;
  isOpen: boolean;
  newName?: string;
  newPassword?: string;
  newIsAdmin?: boolean;
}


const CreateUserModal = ({
  isOpen,
  username,
  password,
  isAdmin,
  error,
  onSubmit,
  onChange,
  onClose
}: {
  isOpen: boolean;
  username: string;
  password: string;
  isAdmin: boolean;
  error: string | null;
  onSubmit: (e: React.FormEvent) => void;
  onChange: (changes: Partial<CreateUserModal>) => void;
  onClose: () => void;
}) => (
  <div className={`modal ${isOpen ? 'show' : ''}`}>
    <div className="modal-content">
      <h2>Create New User</h2>
      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => onChange({ username: e.target.value })}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => onChange({ password: e.target.value })}
            required
          />
        </div>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => onChange({ isAdmin: e.target.checked })}
            />
            Admin User
          </label>
        </div>
        {error && <div className="error-message">{error}</div>}
        <div className="button-group">
          <Button
            type="submit"
            variant="success"
          >
            Create
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  </div>
);

const EditUserModal = ({
  user,
  isOpen,
  error,
  onSubmit,
  onChange,
  onClose
}: {
  user: User | null;
  isOpen: boolean;
  error: string | null;
  onSubmit: (e: React.FormEvent) => void;
  onChange: (changes: Partial<User>) => void;
  onClose: () => void;
}) => (
  <div className={`modal ${isOpen ? 'show' : ''}`}>
    <div className="modal-content">
      <h2>Edit User</h2>
      {user && (
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label htmlFor="edit-username">Username:</label>
            <input
              type="text"
              id="edit-username"
              value={user.name}
              onChange={(e) => onChange({ name: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label htmlFor="edit-cash">Cash:</label>
            <input
              type="number"
              id="edit-cash"
              value={user.cash}
              onChange={(e) => onChange({ cash: parseFloat(e.target.value) })}
              step="0.01"
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <div className="button-group">
            <Button
              type="submit"
              variant="primary"
            >
              Save
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  </div>
);

export function Dashboard() {
  const [users, setUsers] = useState<User[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [createModal, setCreateModal] = useState<CreateUserModal>({
    isOpen: false,
    username: '',
    password: '',
    isAdmin: false
  });
  const [error, setError] = useState<string | null>(null);
  const [deviceWebsockets, setDeviceWebsockets] = useState<{ [key: number]: WebSocket }>({});
  const API_URL = 'http://localhost:8000';
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
      const response = await fetch(`${API_URL}/user/all`, {
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
      const response = await fetch(`${API_URL}/device/all`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to load devices');
      const data = await response.json();
      setDevices(data);
      initializeDeviceWebsockets(data);  // Initialize WebSockets after loading devices
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

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  const handleStopDevice = async (deviceId: number) => {
    try {
      const response = await fetch(`${API_URL}/device/stop/${deviceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to stop device');
    } catch (error) {
      console.error('Error stopping device:', error);
      throw error; // Re-throw to handle in the DeviceCard component
    }
  };

  const handleStartDevice = async (deviceId: number, duration: number) => {
    try {
      const response = await fetch(`${API_URL}/device/start/${deviceId}`, {
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

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/user`, {  // Changed from /user/create to /user
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: createModal.username,      // Changed from username to name to match API
          password: createModal.password,
          is_admin: createModal.isAdmin
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create user');
      }

      // Reset form and close modal
      setCreateModal({
        isOpen: false,
        username: '',
        password: '',
        isAdmin: false
      });

      // Reload users list
      loadUsers();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create user');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/user/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }

      // Reload users list after successful deletion
      loadUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete user');
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    try {
      // Create update payload based on what's changed
      const updateData: {
        name?: string;
        cash?: number;
      } = {};

      // Only include fields that are actually changed
      if (editingUser.name) {
        updateData.name = editingUser.name;
      }
      if (editingUser.cash !== undefined) {
        updateData.cash = editingUser.cash;
      }

      const response = await fetch(`${API_URL}/user/${editingUser.uid}`, {
        method: 'PATCH',  // Changed from PUT to PATCH
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update user');
      }

      setEditingUser(null);
      loadUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      setError(error instanceof Error ? error.message : 'Failed to update user');
    }
  };

  return (
    <div className="dashboard">
      <div className="container">
        <div className="header">
          <h1>Waschsalon Admin Panel</h1>
          <div>
            <Button
              variant="secondary"
              onClick={handleLogout}
              className="ml-2"
            >
              Logout
            </Button>
          </div>
        </div>

        <div className="devices-section">
          <h2>Devices</h2>
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

        <h2>User Management</h2>
        <UserTable
          users={users}
          onEdit={setEditingUser}
          onDelete={handleDeleteUser}
          onRefresh={loadUsers}
          onCreateUser={async (userData) => {
            try {
              const response = await fetch(`${API_URL}/user`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  name: userData.username,
                  password: userData.password,
                  is_admin: userData.isAdmin
                })
              });

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create user');
              }

              await loadUsers();
            } catch (error) {
              throw error instanceof Error ? error : new Error('Failed to create user');
            }
          }}
        />

        <CreateUserModal
          isOpen={createModal.isOpen}
          username={createModal.username}
          password={createModal.password}
          isAdmin={createModal.isAdmin}
          error={error}
          onSubmit={handleCreateUser}
          onChange={(changes) => setCreateModal({ ...createModal, ...changes })}
          onClose={() => setCreateModal({ ...createModal, isOpen: false })}
        />

        <EditUserModal
          user={editingUser}
          isOpen={!!editingUser}
          error={error}
          onSubmit={handleEditUser}
          onChange={(changes) => setEditingUser(prev => prev ? { ...prev, ...changes } : null)}
          onClose={() => setEditingUser(null)}
        />
      </div>
    </div>
  );
}
