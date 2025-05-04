import { useState, useEffect } from 'react';
import { Button } from '../Button/Button';
import { ProfileAttribute } from './ProfileAttribute';
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


  useEffect(() => {
    setIsLoading(true);
    userService.getCurrentUser(true).then(setUser).catch(setError);
    setIsLoading(false);
  }, []);


  const handleUpdateUsername = async (newUsername: string) => {
    try {
      const updatedUser = await userService.updateCurrentUsersUsername(newUsername);
      setUser(updatedUser);
      setSuccess('Username updated successfully');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update username');
    }
  };

  const handleChangePassword = () => {
    setShowPasswordModal(true);
  };

  // Add a new function to handle keycard removal
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
          <ProfileAttribute
            label="User ID"
            value={user.uid}
          />

          <ProfileAttribute
            label="Username"
            value={user.name}
            isEditable={true}
            onUpdate={handleUpdateUsername}
          />

          <ProfileAttribute
            label="Balance"
            value={`€${user.cash.toFixed(2)}`}
          />

          <ProfileAttribute
            label="Admin"
            value={user.is_admin ? 'Yes' : 'No'}
          />

          <div className="profile-attribute-row">
            <ProfileAttribute
              label="Key Card"
              value={user.has_keycard ? 'Linked' : 'Not Linked'}
            />
            {user.has_keycard && (
              <Button
                variant="danger"
                onClick={handleRemoveKeycard}
                disabled={isLoading}
              >
                Remove Key Card
              </Button>
            )}
          </div>

          <ProfileAttribute
            label="Account Created"
            value={new Date(user.creation_time).toLocaleString()}
          />

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
