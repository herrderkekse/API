import { useState, useEffect } from 'react';
import { Button } from '../Button/Button';
import { ProfileAttribute } from './ProfileAttribute';
import './ProfileScreen.css';

interface User {
  uid: number;
  name: string;
  cash: number;
  is_admin: boolean;
  creation_time: string;
  has_keycard: boolean;
}

export function ProfileScreen() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const API_URL = 'http://localhost:8000';
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    setIsLoading(true);
    try {
      // First get the user ID from the token
      const userResponse = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user information');
      }

      const userData = await userResponse.json();
      setUser(userData);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to load profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateUsername = async (newUsername: string) => {
    if (!user) throw new Error('User not found');

    setError(null);
    setSuccess(null);

    const response = await fetch(`${API_URL}/user/${user.uid}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: newUsername
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update username');
    }

    const updatedUser = await response.json();
    setUser(updatedUser);
    setSuccess('Profile updated successfully');
  };

  const handleChangePassword = () => {
    setShowPasswordModal(true);
  };

  // Add a new function to handle keycard removal
  const handleRemoveKeycard = async () => {
    if (!user) return;

    if (!window.confirm('Are you sure you want to remove your linked key card?')) {
      return;
    }

    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/user/${user.uid}/keycard`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove key card');
      }

      // Reload user profile to update the UI
      await loadUserProfile();
      setSuccess('Key card removed successfully');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to remove key card');
    } finally {
      setIsLoading(false);
    }
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
