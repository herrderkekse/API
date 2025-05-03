import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import './style.css';

export function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [incorrectFields, setIncorrectFields] = useState<{
    username: boolean;
    password: boolean;
  }>({ username: false, password: false });

  const validateForm = (): string[] => {
    const errors: string[] = [];
    const newIncorrectFields = { username: false, password: false };

    if (username === '' || username == null) {
      errors.push('Username is required');
      newIncorrectFields.username = true;
    }

    if (password === '' || password == null) {
      errors.push('Password is required');
      newIncorrectFields.password = true;
    }

    setIncorrectFields(newIncorrectFields);
    return errors;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const errors = validateForm();

    if (errors.length > 0) {
      setError(errors.join('. '));
      return;
    }

    setError(null);
    setIsLoading(true);

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch('http://172.18.79.254:8000/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      localStorage.setItem('token', data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: 'username' | 'password', value: string) => {
    if (field === 'username') {
      setUsername(value);
    } else {
      setPassword(value);
    }

    if (incorrectFields[field]) {
      setIncorrectFields({ ...incorrectFields, [field]: false });
      setError(null);
    }
  };

  return (
    <div className="login-page">
      <div className="wrapper">
        <h1>Login</h1>
        {error && <p id="error-message">{error}</p>}
        <form id="form" onSubmit={handleSubmit}>
          <div className={incorrectFields.username ? 'incorrect' : ''}>
            <label htmlFor="username-input">
              <span>@</span>
            </label>
            <input
              type="text"
              name="username"
              id="username-input"
              placeholder="Username"
              value={username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className={incorrectFields.password ? 'incorrect' : ''}>
            <label htmlFor="password-input">
              <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24">
                <path d="M240-80q-33 0-56.5-23.5T160-160v-400q0-33 23.5-56.5T240-640h40v-80q0-83 58.5-141.5T480-920q83 0 141.5 58.5T680-720v80h40q33 0 56.5 23.5T800-560v400q0 33-23.5 56.5T720-80H240Zm240-200q33 0 56.5-23.5T560-360q0-33-23.5-56.5T480-440q-33 0-56.5 23.5T400-360q0 33 23.5 56.5T480-280ZM360-640h240v-80q0-50-35-85t-85-35q-50 0-85 35t-35 85v80Z" />
              </svg>
            </label>
            <input
              type="password"
              name="password"
              id="password-input"
              placeholder="Password"
              value={password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              disabled={isLoading}
            />
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p>New here? <a href="signup">Create an Account</a></p>
      </div>
    </div>
  );
}
