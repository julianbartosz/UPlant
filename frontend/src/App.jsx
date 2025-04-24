// frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DashboardPage, CatalogPage, SettingsPage, NotificationsPage } from './pages';
import { LoadingAnimation } from './components/layout';
import UserProvider from './contexts/UserProvider';
import WeatherWidget from './components/widgets/WeatherWidget';
import './styles/app.css';
import { useState, useEffect } from 'react';
import LoginModal from './pages/LoginModal';
import SignupPage from './pages/SignupModal';

const getCSRFToken = async () => {
  const response = await fetch('http://localhost:8000/api/notifications/notifications/', {  // Updated endpoint to match the CSRF token route
    'credentials': 'include',
  });
  console.log(response.status);
  const data = await response.json();
  console.log(data);
};

function App() {
  const [csrfToken, setCsrfToken] = useState('');

  const handleGetCsrfToken = async () => {
    const token = await getCSRFToken();
    setCsrfToken(token);
  };

  useEffect(() => {
    if (csrfToken) {
      console.log(`CSRF Token: ${csrfToken}`);
    }
    else {
      console.log('CSRF Token not set');
    }
  }
  , [csrfToken]);

  return (
    <UserProvider>
      <Router basename='/app'>
        <Routes>
          <Route 
            path="/csrf-token" 
            element={
              <div>
                <button onClick={handleGetCsrfToken}>Get CSRF Token</button>
                {csrfToken && <p>CSRF Token: {csrfToken}</p>}
              </div>
            } 
          />
          <Route path="/" element={<LoadingAnimation redirect="/dashboard"/>} />
          <Route path="/login" element={<LoginModal />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/catalog" element={<CatalogPage/>} />
          <Route path="/settings" element={<SettingsPage/>} />
          <Route path="/notifications" element={<NotificationsPage/>} />
          <Route path="*" element={<div className='centered-message'>Oops! Looks like you've wandered off the garden path.</div>} />
          {/* <Route path="/weather" element={<div style={{background: 'lightblue'}}><WeatherWidget /></div>} /> */}
        </Routes>
      </Router>
    </UserProvider>
  );
}

export default App;
