import { useEffect, useState } from 'react';
import './Dashboard.css';

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
  time_left: number;
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
          <button type="submit" className="button create-button">Create</button>
          <button
            type="button"
            onClick={onClose}
            className="button cancel-button"
          >
            Cancel
          </button>
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
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="edit-password">New Password (optional):</label>
            <input
              type="password"
              id="edit-password"
              placeholder="Leave blank to keep current password"
              onChange={(e) => onChange({ password: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={user.is_admin}
                onChange={(e) => onChange({ is_admin: e.target.checked })}
              />
              Admin User
            </label>
          </div>
          {error && <div className="error-message">{error}</div>}
          <div className="button-group">
            <button type="submit" className="button edit-button">Save</button>
            <button
              type="button"
              onClick={onClose}
              className="button cancel-button"
            >
              Cancel
            </button>
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

  const API_URL = 'http://localhost:8000';
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadUsers();
    loadDevices();
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
    } catch (error) {
      console.error('Error loading devices:', error);
    }
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
      loadDevices();
    } catch (error) {
      console.error('Error stopping device:', error);
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
      const response = await fetch(`${API_URL}/user/${editingUser.uid}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: editingUser.name,
          password: (editingUser as any).password, // Only included if changed
          is_admin: editingUser.is_admin
        })
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
            <button
              onClick={() => setCreateModal({ ...createModal, isOpen: true })}
              className="button create-button"
            >
              Create User
            </button>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>

        <div className="devices-section">
          <h2>Device Status</h2>
          <div className="device-grid">
            {devices.map(device => (
              <div key={device.id} className="device-card" data-device-id={device.id}>
                <h3>
                  {device.name}
                  <span className="device-type">{device.type}</span>
                </h3>
                <p>Cost: ${device.hourly_cost}/hour</p>
                <p className={`device-status ${device.user_id ? 'status-in-use' : 'status-available'}`}>
                  {device.user_id ? 'In Use' : 'Available'}
                </p>
                <p className="time-left">Time Left: {Math.round(device.time_left)} seconds</p>
                {device.user_id && (
                  <>
                    <p className="user-info">User ID: {device.user_id}</p>
                    <button
                      onClick={() => handleStopDevice(device.id)}
                      className="button stop-button"
                    >
                      Stop Device
                    </button>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        <h2>User Management</h2>
        <table className="user-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Cash</th>
              <th>Admin</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.uid}>
                <td>{user.uid}</td>
                <td>{user.name}</td>
                <td>{user.cash.toFixed(2)}</td>
                <td>{user.is_admin ? 'Yes' : 'No'}</td>
                <td>{new Date(user.creation_time).toLocaleString()}</td>
                <td>
                  <button
                    onClick={() => setEditingUser(user)}
                    className="button edit-button"
                  >
                    Edit
                  </button>
                  {!user.is_admin && (
                    <button
                      onClick={() => handleDeleteUser(user.uid)}
                      className="button delete-button"
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

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
