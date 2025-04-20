// frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DashboardPage, CatalogPage, SettingsPage, NotificationsPage } from './pages';
import { LoadingAnimation } from './components/layout';
import UserProvider from './contexts/UserProvider';
import './styles/app.css';

function App() {

  return (
    <UserProvider>
      <Router basename='/app'>
        <Routes>

          <Route path="/" element={<LoadingAnimation redirect="/dashboard"/>} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/catalog" element={<CatalogPage/>} />
          <Route path="/settings" element={<SettingsPage/>} />
          <Route path="/notifications" element={<NotificationsPage/>} />
          <Route path="*" element={<div className='centered-message'>Oops! Looks like you've wandered off the garden path.</div>} />

        </Routes>
      </Router>
    </UserProvider>
  );
}

export default App;
