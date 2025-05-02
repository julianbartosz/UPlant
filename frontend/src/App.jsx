import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import { DashboardPage, CatalogPage, SettingsPage, NotificationsPage } from './pages';
import UserProvider from './context/UserProvider';
import { DashboardPage } from './pages';
import './styles/app.css';
import { useState, useEffect } from 'react';
import { NotificationList } from './components/layout';
import { UserContext } from './context/UserProvider';
import NotificationsPage from './pages/NotificationsPage';

import SettingsPage from './pages/SettingsPage';

function App() {

const fetchDetails = async () => {
  const response = await fetch('http://localhost:8000/api/notifications/notifications/5688/', {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  console.log("DATA((((((((",data);
};



  return (
    <UserProvider>
      <Router basename='/app'>
        <Routes>
          <Route path="/fetch-details" element={
            <div className="centered-message">
              <button onClick={fetchDetails}>Fetch Details</button>
              <NotificationList />
            </div>
          } />
          <Route path="/dashboard" element={<DashboardPage />} />
          {/* <Route path="/catalog" element={<CatalogPage />} />  */}
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="*" element={
            <div className='centered-message'>Oops! Looks like you've wandered off the garden path.</div>} />
        </Routes>
      </Router>
    </UserProvider>
  );
}

export default App;