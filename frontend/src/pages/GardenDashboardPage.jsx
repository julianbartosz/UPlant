// frontend/src/pages/GardenDashboardPage.jsx

import React from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { GardenSection, NavBarSection, PlantSearchSection } from '../components/sections/index.js';
import { useUser } from '../contexts/ProtectedRoute.jsx';

function GardenDashboard() {
    // Use the useUser hook to get user data
    const { user } = useUser();
    
    console.log('User context data:', user); // Debug log
    
    // Show loading state while waiting for user data
    if (!user) {
      return <p>Loading user data...</p>;
    }
    
    console.log("GardenDashboard user:", user);

    return (
      <div style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
        {/* Navigation bar at the top */}
        <NavBarSection user={user} />
        <DndProvider backend={HTML5Backend}>
        {/* Sidebar with plant search functionality */}
        <div className="sidebar" style={{
          position: 'fixed', 
          top: '60px', 
          left: 0, 
          width: '200px', 
          height: 'calc(100vh - 60px)',
          background: 'linear-gradient(to right, rgb(152, 152, 152), rgb(65, 64, 64))', 
          padding: '10px', 
          zIndex: 5,
          borderRadius: '0 10px 0 0'
        }}>
          <PlantSearchSection />
        </div>
        
        {/* Main content area with garden visualization */}
        <div style={{
          position: 'fixed', 
          top: '60px', 
          left: '240px', 
          width: 'calc(100vw - 240px)',
          height: 'calc(100vh - 60px)', 
          background: 'white',
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
        }}>
          <GardenSection user={user} />
        </div>
        </DndProvider>
      </div>
    );
}

export default GardenDashboard;