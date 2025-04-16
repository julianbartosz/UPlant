

import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { GardenSection, NavBarSection, PlantSearchSection } from '../components/sections';
import { useUser } from '../hooks/useUser';


function GardenDashboard() {

    const { username, usernameLoading, usernameError} = useUser();

    if (usernameError) {
      return <p>Error loading user data: {usernameError}</p>;
    }

    if (usernameLoading) {
      return <p>Loading user data...</p>;
    }
    
    console.log("GardenDashboard user:", username);

  return (
    <>
    <div style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
    <NavBarSection title="Dashboard" username={username} onBack={ () => { window.location.href = 'http://localhost:8000/' } } />
      
      <DndProvider backend={HTML5Backend}>
        <div className="sidebar" style={{
          position: 'fixed', top: '60px', left: 0, width: '200px', height: 'calc(100vh - 60px)',
          background: 'linear-gradient(to right, rgb(152, 152, 152),rgb(65, 64, 64))', padding: '10px', zIndex: 5
          , borderRadius: '0 10px 0 0'
        }}>
          <PlantSearchSection />
        </div>
        <div  style={{
          position: 'fixed', top: '60px', left: '240px', width: 'calc(100vw - 200px)',
          height: 'calc(100vh - 60px)', background: 'white',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
        }}>
          <GardenSection/>
        </div>
      </DndProvider>
    </div>
    </>
  )
}

export default GardenDashboard;