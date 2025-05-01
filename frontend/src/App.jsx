// frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import { DashboardPage, CatalogPage, SettingsPage, NotificationsPage } from './pages';
import UserProvider from './context/UserProvider';
import { DashboardPage } from './pages';
import './styles/app.css';

import SettingsPage from './pages/SettingsPage';

function App() {
  
    return (
    <UserProvider>
      <Router basename='/app'>
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          {/* <Route path="/catalog" element={<CatalogPage />} />  */}
          <Route path="/settings" element={<SettingsPage />} />
          {/* <Route path="/notifications" element={<NotificationsPage />} /> */}
          <Route path="*" element={
            <div className='centered-message'>Oops! Looks like you've wandered off the garden path.</div>} />
        </Routes>
      </Router>
    </UserProvider>
  );
}

export default App;