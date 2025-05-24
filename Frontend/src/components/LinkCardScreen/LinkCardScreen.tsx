import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import './LinkCardScreen.css';
import { API_BASE_URL } from '../../config';

export function LinkCardScreen() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const urlToken = searchParams.get('token') || 'No token provided';
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [linkStatus, setLinkStatus] = useState<string | null>(null);
  const [pin, setPin] = useState('');
  const [userId, setUserId] = useState<number | null>(null);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
      // Get current user info
      fetchUserInfo(token);
    } else {
      // Redirect to login page if not logged in
      navigate('/', { state: { returnUrl: `/link-card?token=${urlToken}` } });
    }
  }, [navigate, urlToken]);

  const fetchUserInfo = async (token: string) => {
    try {
      const response = await fetch(API_BASE_URL + '/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUserId(userData.uid);
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error);
    }
  };

  const handleLinkToken = async () => {
    if (!pin) {
      setLinkStatus('Error: PIN is required');
      return;
    }

    if (!userId) {
      setLinkStatus('Error: User information not available');
      return;
    }

    setLinkStatus(null);
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(API_BASE_URL + `/user/${userId}/keycard`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          key_card_id: urlToken,
          pin: pin
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to link key card');
      }

      setLinkStatus('Key card linked successfully!');
    } catch (err) {
      setLinkStatus(`Error: ${err instanceof Error ? err.message : 'An error occurred'}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isLoggedIn) {
    return null; // Don't render anything while redirecting
  }

  return (
    <div className="link-card-container">
      <h1>Link Card</h1>
      <div className="token-display">
        <h2>Token:</h2>
        <p>{urlToken}</p>
      </div>

      <div className="link-section">
        <div className="form-group">
          <label htmlFor="pin">Enter PIN for your key card:</label>
          <input
            type="password"
            id="pin"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="Enter 4-digit PIN"
            maxLength={4}
            disabled={isLoading}
          />
        </div>

        <button
          onClick={handleLinkToken}
          disabled={isLoading || !pin}
          className="link-button"
        >
          {isLoading ? 'Linking...' : 'Link Key Card'}
        </button>
        {linkStatus && <p className={linkStatus.includes('Error') ? 'error-message' : 'success-message'}>{linkStatus}</p>}
        <button
          onClick={() => navigate('/dashboard')}
          className="dashboard-button"
        >
          Go to Dashboard
        </button>
      </div>
    </div>
  );
}
