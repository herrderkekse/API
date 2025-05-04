import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Login } from './components/LoginScreen/Login';
import { Signup } from './components/LoginScreen/Signup';
import { Layout } from './components/Layout/Layout';
import { DeviceScreen } from './components/DeviceScreen/DeviceScreen';
import { StatisticsScreen } from './components/StatisticsScreen/StatisticsScreen';
import { UserManagementScreen } from './components/UserManagement/UserManagementScreen';
import { ProfileScreen } from './components/Profile/ProfileScreen';
import { LinkCardScreen } from './components/LinkCardScreen/LinkCardScreen';
import './App.css';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';


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
            <ProtectedRoute>
              <Layout>
                <DeviceScreen />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <Layout>
                <UserManagementScreen />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/statistics"
          element={
            <ProtectedRoute>
              <Layout>
                <StatisticsScreen />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Layout>
                <ProfileScreen />
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
