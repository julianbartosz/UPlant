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


function App() {

  function handlePasswordChange(old, newP, newConfirm) {
    if (newP !== newConfirm) {
      alert("New password and confirmation do not match.");
      return;
    }
    if (newP.length < 8) {
      alert("New password must be at least 8 characters long.");
      return;
    }
    if (old === newP) {
      alert("New password cannot be the same as the old password.");
      return;
    }
    // Proceed with password change logic
    fetch('http://localhost:8000/api/users/password/change/', {
      method: 'POST',
      credentials: 'include',
      headers: {
      'Content-Type': 'application/json',
      },
      body: JSON.stringify({
      current_password: old,
      new_password: newP,
      confirm_password: newConfirm,
      }),
    })
    .then(response => {
      if (!response.ok) {
      throw new Error('Failed to change password');
      }
      return response.json();
    })
    .then(data => {
      alert('Password changed successfully!');
      console.log(data);
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while changing the password.');
    });
  }

  // handlePasswordChange("asdfghjkl;'", "asdfghjkl;", "asdfghjkl;");

 
  return (
    <UserProvider>
      <Router basename='/app'>
        <Routes>
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
