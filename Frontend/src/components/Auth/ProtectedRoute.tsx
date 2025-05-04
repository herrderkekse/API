import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    // Redirect to login page but save the location they were trying to access
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}