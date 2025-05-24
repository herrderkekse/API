import { useState, useEffect } from 'react';
import { Button } from '../Button/Button';
import './ProfileScreen.css';
import { User } from '../../models/user';
import { userService } from '../../services/userService';
import { authService } from '../../services/authService';

export function ProfileScreen() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    setIsLoading(true);
    userService.getCurrentUser(true).then(setUser).catch(setError);
    setIsLoading(false);
  }, []);

  const handleEdit = (field: string, value: string) => {
    setEditingField(field);
    setInputValue(value);
  };

  const handleCancel = () => {
    setEditingField(null);
  };

  const handleSave = async () => {
    if (editingField === 'username') {
      try {
        const updatedUser = await userService.updateCurrentUsersUsername(inputValue);
        setUser(updatedUser);
        setSuccess('Username updated successfully');
        setEditingField(null);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to update username');
      }
    }
  };

  const handleRemoveKeycard = async () => {
    authService.removeCurrentUsersKeycard().then(() => {
      setSuccess('Key card removed successfully');
      userService.clearUserCache();
      setIsLoading(true);
      userService.getCurrentUser(true).then(setUser).catch(setError);
      setIsLoading(false);
    }).catch((error) => {
      setError(error instanceof Error ? error.message : 'Failed to remove key card');
    });
  };

  const handleChangePassword = () => {
    setShowPasswordModal(true);
  };

  if (isLoading && !user) {
    return <div className="profile-screen">Loading profile...</div>;
  }

  return (
    <div className="profile-screen">
      <h2>Your Profile</h2>

      {success && <div className="success-message">{success}</div>}
      {error && <div className="error-message">{error}</div>}

      {user && (
        <div className="profile-info">
          <table className="profile-table">
            <tbody>
              <tr>
                <td className="attribute-label">User ID</td>
                <td className="attribute-value">{user.uid}</td>
                <td className="attribute-action"></td>
              </tr>

              <tr>
                <td className="attribute-label">Username</td>
                <td className="attribute-value">
                  {editingField === 'username' ? (
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      className="attribute-input"
                    />
                  ) : (
                    user.name
                  )}
                </td>
                <td className="attribute-action">
                  {editingField === 'username' ? (
                    <div className="button-group">
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleSave}
                      >
                        Save
                      </Button>
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={handleCancel}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="secondary"
                      size="small"
                      onClick={() => handleEdit('username', user.name)}
                    >
                      Edit
                    </Button>
                  )}
                </td>
              </tr>

              <tr>
                <td className="attribute-label">Balance</td>
                <td className="attribute-value">{`€${user.cash.toFixed(2)}`}</td>
                <td className="attribute-action"></td>
              </tr>

              <tr>
                <td className="attribute-label">Admin</td>
                <td className="attribute-value">{user.is_admin ? 'Yes' : 'No'}</td>
                <td className="attribute-action"></td>
              </tr>

              <tr>
                <td className="attribute-label">Key Card</td>
                <td className="attribute-value">{user.has_keycard ? 'Linked' : 'Not Linked'}</td>
                <td className="attribute-action">
                  {user.has_keycard && (
                    <Button
                      variant="danger"
                      size="small"
                      onClick={handleRemoveKeycard}
                      disabled={isLoading}
                    >
                      Remove
                    </Button>
                  )}
                </td>
              </tr>

              <tr>
                <td className="attribute-label">Account Created</td>
                <td className="attribute-value">{new Date(user.creation_time).toLocaleString()}</td>
                <td className="attribute-action"></td>
              </tr>
            </tbody>
          </table>

          <div className="password-section">
            <Button
              variant="secondary"
              onClick={handleChangePassword}
            >
              Change Password
            </Button>
          </div>
        </div>
      )}

      {showPasswordModal && (
        <div className="password-modal">
          <div className="password-modal-content">
            <h3>Change Password</h3>
            <p className="not-implemented-message">
              This feature is not implemented yet. The backend doesn't currently support password changes.
            </p>
            <Button
              variant="primary"
              onClick={() => setShowPasswordModal(false)}
            >
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
