
import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import './style.css';
import { userService } from '../../services/userService';
import { authService } from '../../services/authService';

export function Signup() {
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [repeatPassword, setRepeatPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [incorrectFields, setIncorrectFields] = useState<{
        firstname: boolean;
        username: boolean;
        password: boolean;
        repeatPassword: boolean;
    }>({ firstname: false, username: false, password: false, repeatPassword: false });

    const validateForm = (): string[] => {
        const errors: string[] = [];
        const newIncorrectFields = {
            firstname: false,
            username: false,
            password: false,
            repeatPassword: false
        };

        if (username === '' || username == null) {
            errors.push('Username is required');
            newIncorrectFields.username = true;
            // } else if (!/\S+@\S+\.\S+/.test(username)) {
            //     errors.push('Username is invalid');
            //     newIncorrectFields.username = true;
        }

        if (password === '' || password == null) {
            errors.push('Password is required');
            newIncorrectFields.password = true;
        }

        if (repeatPassword === '' || repeatPassword == null) {
            errors.push('Please repeat your password');
            newIncorrectFields.repeatPassword = true;
        } else if (password !== repeatPassword) {
            errors.push('Passwords do not match');
            newIncorrectFields.repeatPassword = true;
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

        try {
            await userService.createUser(username, password);
            await authService.login(username, password);
            // Redirect to dashboard after successful signup
            navigate('/dashboard');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    const handleInputChange = (
        field: 'firstname' | 'username' | 'password' | 'repeatPassword',
        value: string
    ) => {
        if (field === 'username') {
            setUsername(value);
        } else if (field === 'password') {
            setPassword(value);
        } else {
            setRepeatPassword(value);
        }

        if (incorrectFields[field]) {
            setIncorrectFields({ ...incorrectFields, [field]: false });
            setError(null);
        }
    };

    return (
        <div className="login-page">
            <div className="wrapper">
                <h1>Signup</h1>
                {error && <p id="error-message">{error}</p>}
                <form id="form" onSubmit={handleSubmit}>
                    <div className={incorrectFields.username ? 'incorrect' : ''}>
                        <label htmlFor="username-input">
                            <span>@</span>
                        </label>
                        <input
                            type="username"
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
                    <div className={incorrectFields.repeatPassword ? 'incorrect' : ''}>
                        <label htmlFor="repeat-password-input">
                            <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24">
                                <path d="M240-80q-33 0-56.5-23.5T160-160v-400q0-33 23.5-56.5T240-640h40v-80q0-83 58.5-141.5T480-920q83 0 141.5 58.5T680-720v80h40q33 0 56.5 23.5T800-560v400q0 33-23.5 56.5T720-80H240Zm240-200q33 0 56.5-23.5T560-360q0-33-23.5-56.5T480-440q-33 0-56.5 23.5T400-360q0 33 23.5 56.5T480-280ZM360-640h240v-80q0-50-35-85t-85-35q-50 0-85 35t-35 85v80Z" />
                            </svg>
                        </label>
                        <input
                            type="password"
                            name="repeat-password"
                            id="repeat-password-input"
                            placeholder="Repeat Password"
                            value={repeatPassword}
                            onChange={(e) => handleInputChange('repeatPassword', e.target.value)}
                            disabled={isLoading}
                        />
                    </div>
                    <button type="submit" disabled={isLoading}>
                        {isLoading ? 'Signing up...' : 'Signup'}
                    </button>
                </form>
                <p>Already have an Account? <a href="/">Login</a></p>
            </div>
        </div>
    );
}

