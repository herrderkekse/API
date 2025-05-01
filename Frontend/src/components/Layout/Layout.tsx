import { ReactNode, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../Button/Button';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(location.pathname);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleTabChange = (path: string) => {
    setActiveTab(path);
    navigate(path);
  };

  return (
    <div className="admin-layout">
      <div className="container">
        <div className="header">
          <h1>Waschsalon Admin Panel</h1>
          <div>
            <Button
              variant="secondary"
              onClick={handleLogout}
              className="ml-2"
            >
              Logout
            </Button>
          </div>
        </div>
        <div className="tab-bar">
          <div
            className={`tab ${activeTab === '/dashboard' ? 'active' : ''}`}
            onClick={() => handleTabChange('/dashboard')}
          >
            Devices
          </div>
          <div
            className={`tab ${activeTab === '/users' ? 'active' : ''}`}
            onClick={() => handleTabChange('/users')}
          >
            User Management
          </div>
          <div
            className={`tab ${activeTab === '/statistics' ? 'active' : ''}`}
            onClick={() => handleTabChange('/statistics')}
          >
            Statistics
          </div>
          <div
            className={`tab ${activeTab === '/profile' ? 'active' : ''}`}
            onClick={() => handleTabChange('/profile')}
          >
            Profile
          </div>
        </div>
        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
}
