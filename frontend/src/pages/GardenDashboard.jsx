// frontend/src/pages/GardenDashboard.jsx

import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import Garden from '../components/GardenSection/Garden'
import NavBar from '../components/NavBarSection/NavBar';
import SearchPlants from '../components/SearchSection/SearchPlants'
import { useState } from 'react';
import { useUser } from '../contexts/ProtectedRoute.jsx';

function GardenDashboard() {

    const userContext = useUser();
    const user = userContext?.user; // Use optional chaining
    console.log('userContext:', userContext); // See what's actually being returned
    
    if (!user) {
      return <p>Loading user data...</p>;
    }
    
    console.log("GardenDashboard user:", user);
  // TODO: Retrieve user info and authentication token from login redirect

  return (
    <div className='app' style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
      <NavBar user = {user}/>
      <DndProvider backend={HTML5Backend}>
        <div className="sidebar" style={{
          position: 'fixed', top: '60px', left: 0, width: '200px', height: 'calc(100vh - 60px)',
          background: 'linear-gradient(to right, rgb(152, 152, 152),rgb(65, 64, 64))', padding: '10px', zIndex: 5
          , borderRadius: '0 10px 0 0'
        }}>

          <SearchPlants />

        </div>
        <div  style={{
          position: 'fixed', top: '60px', left: '240px', width: 'calc(100vw - 200px)',
          height: 'calc(100vh - 60px)', background: 'white',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
        }}>
          <Garden user={user}/>
        </div>
      </DndProvider>
    </div>
  )
}

export default GardenDashboard;