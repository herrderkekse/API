import { useState, useEffect } from 'react';
import { Button } from '../Button/Button';
import { UserTable } from '../UserTable/UserTable';
import './UserManagementScreen.css';
import { API_BASE_URL } from '../../config';

interface User {
  uid: number;
  name: string;
  cash: number;
  is_admin: boolean;
  creation_time: string;
  has_keycard: boolean;
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

export function UserManagementScreen() {
  const [users, setUsers] = useState<User[]>([]);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [createModal, setCreateModal] = useState<CreateUserModal>({
    isOpen: false,
    username: '',
    password: '',
    isAdmin: false
  });
  const [error, setError] = useState<string | null>(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadUsers();
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

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/user`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: createModal.username,
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
      const response = await fetch(`${API_BASE_URL}/user/${userId}`, {
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

      const response = await fetch(`${API_BASE_URL}/user/${editingUser.uid}`, {
        method: 'PATCH',
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
    <div className="user-management-screen">
      <div className="user-management-header">
        <h2>Currently Resistered Users</h2>
        <Button
          variant="primary"
          onClick={() => setCreateModal({ isOpen: true, username: '', password: '', isAdmin: false })}
        >
          Create User
        </Button>
      </div>

      <UserTable
        users={users}
        onEdit={(user) => setEditingUser(user)}
        onDelete={handleDeleteUser}
        onRefresh={loadUsers}
        onCreateUser={async (userData) => {
          try {
            await fetch(`${API_BASE_URL}/user`, {
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
            await loadUsers();
          } catch (error) {
            throw error;
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
  );
}
