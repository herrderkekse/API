import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './components/LoginScreen/Login';
import { Signup } from './components/LoginScreen/Signup';
import { Layout } from './components/Layout/Layout';
import { DeviceScreen } from './components/DeviceScreen/DeviceScreen';
import { StatisticsScreen } from './components/StatisticsScreen/StatisticsScreen';
import { UserManagementScreen } from './components/UserManagement/UserManagementScreen';
import { ProfileScreen } from './components/Profile/ProfileScreen';
import { LinkCardScreen } from './components/LinkCardScreen/LinkCardScreen';
import './App.css';


function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/" />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/link-card" element={<LinkCardScreen />} />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Layout>
                <DeviceScreen />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/users"
          element={
            <PrivateRoute>
              <Layout>
                <UserManagementScreen />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/statistics"
          element={
            <PrivateRoute>
              <Layout>
                <StatisticsScreen />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <PrivateRoute>
              <Layout>
                <ProfileScreen />
              </Layout>
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
