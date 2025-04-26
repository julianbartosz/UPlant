// frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import GardenDashboard from './pages/GardenDashboardPage.jsx';
import Catalog from './pages/CatalogPage.jsx'; 
import UserProvider from './contexts/UserProvider.jsx';
import SettingsPage from './pages/SettingsPage.jsx';
import './styles/app.css';

function App() {
  console.log("App component rendering");
  
  return (
    <UserProvider>
    <DndProvider backend={HTML5Backend}>
      <Router basename='/app'>
        <Routes>
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/home" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<GardenDashboard />} />
          <Route path="/catalog" element={<Catalog/>} />
          <Route path="/settings" element={<SettingsPage/>} />
          <Route path="*" element={<div>Page not found</div>} />

        </Routes>
      </Router>
    </DndProvider>
    </UserProvider>
  );
}

export default App;