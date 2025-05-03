import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import './LinkCardScreen.css';

export function LinkCardScreen() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const urlToken = searchParams.get('token') || 'No token provided';
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [linkStatus, setLinkStatus] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
    } else {
      // Redirect to login page if not logged in
      navigate('/', { state: { returnUrl: `/link-card?token=${urlToken}` } });
    }
  }, [navigate, urlToken]);

  const handleLinkToken = async () => {
    setLinkStatus(null);
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/device/link', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: urlToken }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to link token');
      }

      setLinkStatus('Token linked successfully!');
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
        <button
          onClick={handleLinkToken}
          disabled={isLoading}
          className="link-button"
        >
          {isLoading ? 'Linking...' : 'Link Token'}
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
