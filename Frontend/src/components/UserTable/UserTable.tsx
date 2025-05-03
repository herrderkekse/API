import { useState } from 'react';
import { Button } from '../Button/Button';
import './UserTable.css';

interface User {
  uid: number;
  name: string;
  cash: number;
  is_admin: boolean;
  creation_time: string;
  has_keycard: boolean;
}

interface UserTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (userId: number) => void;
  onRefresh: () => Promise<void>;
  onCreateUser: (userData: { username: string; password: string; isAdmin: boolean }) => Promise<void>;
}


export function UserTable({ users, onEdit, onDelete, onRefresh }: UserTableProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };


  return (
    <div className="user-table-container">
      <table className="user-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Cash</th>
            <th>Admin</th>
            <th>Key Card</th>
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
              <td>{user.has_keycard ? 'Yes' : 'No'}</td>
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
    </div>
  );
}
