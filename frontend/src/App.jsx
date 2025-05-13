import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DashboardPage, NotificationsPage, CatalogPage, SettingsPage } from './pages';
import { Navigate } from 'react-router-dom';
import UserProvider from './context/UserProvider';
import './styles/app.css';

const AccountAccess = ({ children }) => (
  <UserProvider>
    {children}
  </UserProvider>
);

const ProtectedDashboard = () => (
  <AccountAccess>
    <DashboardPage />
  </AccountAccess>
);

const ProtectedSettings = () => (
  <AccountAccess>
    <SettingsPage />
  </AccountAccess>
);

const ProtectedNotifications = () => (
  <AccountAccess>
    <NotificationsPage />
  </AccountAccess>
);

function App() {
  return (
    <Router basename='/app'>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<ProtectedDashboard />} />
        <Route path="/settings" element={<ProtectedSettings />} />
        <Route path="/notifications" element={<ProtectedNotifications />} />
        <Route path="/catalog" element={<CatalogPage />} /> 
      </Routes>
    </Router>
  );
}

export default App;