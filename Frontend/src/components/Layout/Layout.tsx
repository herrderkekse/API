import { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../Button/Button';
import './Layout.css';

interface AdminLayoutProps {
  children: ReactNode;
}

export function AdminLayout({ children }: AdminLayoutProps) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
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
        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
}
