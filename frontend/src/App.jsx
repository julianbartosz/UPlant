import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DashboardPage, NotificationsPage, CatalogPage, SettingsPage } from './pages';
import { Navigate } from 'react-router-dom';
import UserProvider from './context/UserProvider';
import './styles/app.css';

function App() {
  

  return (
    <UserProvider>
      <Router basename='/app'>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/catalog" element={<CatalogPage />} /> 
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
        </Routes>
      </Router>
    </UserProvider>
  );
}

export default App; 