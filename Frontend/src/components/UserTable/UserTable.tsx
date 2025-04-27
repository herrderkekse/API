import { useState } from 'react';
import { Button } from '../Button/Button';
import './UserTable.css';

interface User {
  uid: number;
  name: string;
  cash: number;
  is_admin: boolean;
  creation_time: string;
}

interface UserTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (userId: number) => void;
  onRefresh: () => Promise<void>;
  onCreateUser: (userData: { username: string; password: string; isAdmin: boolean }) => Promise<void>;
}

interface CreateUserModalState {
  isOpen: boolean;
  username: string;
  password: string;
  isAdmin: boolean;
}

export function UserTable({ users, onEdit, onDelete, onRefresh, onCreateUser }: UserTableProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [createModal, setCreateModal] = useState<CreateUserModalState>({
    isOpen: false,
    username: '',
    password: '',
    isAdmin: false
  });
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onCreateUser({
        username: createModal.username,
        password: createModal.password,
        isAdmin: createModal.isAdmin
      });
      setCreateModal({
        isOpen: false,
        username: '',
        password: '',
        isAdmin: false
      });
      setError(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create user');
    }
  };

  return (
    <div className="user-table-container">
      <div className="user-table-header">
        <h2>User Management</h2>
        <Button
          variant="primary"
          onClick={() => setCreateModal({ ...createModal, isOpen: true })}
        >
          Create User
        </Button>
      </div>

      <table className="user-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Cash</th>
            <th>Admin</th>
            <th>Created</th>
            <th className="actions-header">
              Actions
              <Button
                variant="secondary"
                onClick={handleRefresh}
                size="small"
                className="refresh-button"
                isLoading={isRefreshing}
              >
                Refresh
              </Button>
            </th>
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
                <Button
                  variant="primary"
                  onClick={() => onEdit(user)}
                >
                  Edit
                </Button>
                {!user.is_admin && (
                  <Button
                    variant="danger"
                    onClick={() => onDelete(user.uid)}
                    className="ml-2"
                  >
                    Delete
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Create User Modal */}
      <div className={`modal ${createModal.isOpen ? 'show' : ''}`}>
        <div className="modal-content">
          <h2>Create New User</h2>
          <form onSubmit={handleCreateSubmit}>
            <div className="form-group">
              <label htmlFor="username">Username:</label>
              <input
                type="text"
                id="username"
                value={createModal.username}
                onChange={(e) => setCreateModal({ ...createModal, username: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input
                type="password"
                id="password"
                value={createModal.password}
                onChange={(e) => setCreateModal({ ...createModal, password: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={createModal.isAdmin}
                  onChange={(e) => setCreateModal({ ...createModal, isAdmin: e.target.checked })}
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
                onClick={() => setCreateModal({ ...createModal, isOpen: false })}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
