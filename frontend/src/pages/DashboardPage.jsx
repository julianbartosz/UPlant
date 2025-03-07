
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import Garden from '../components/GardenSection/Garden'
import NavBar from '../components/NavBarSection/NavBar';
import SearchPlants from '../components/SearchSection/SearchPlants'
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';


function DashboardPage() {
  
  const fetchUsername = async (token) => {
    try {
      const response = await fetch('/api/user', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,  // Send the token as a Bearer token
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch username');
      }

      const data = await response.json();
      return data.username;  // Return the fetched username
   
    } catch (error) {
      console.error('Error fetching username:', error);
    }
  }

  const fetchGardens = async (token) => {
    try {
      const response = await fetch('/api/gardens', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,  // Send the token as a Bearer token
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch gardens');
      }

      const data = await response.json();
      return data;  // Return the fetched garden data
   
    } catch (error) {
      console.error('Error fetching garden data:', error);
    }
  };
  
    const emptyCells = (x, y) => {
        let cells = [];
        for (let i = 0; i < y; i++) {
            cells.push(Array(x).fill(null));
        }
        return cells;
    }
  const exampleGardens = () => {
    return {
    'Garden 1': { x: 5, y: 5, cells: emptyCells(5,5) },
    'Garden 2': { x: 4, y: 6, cells: emptyCells(6,6) }
    }
}

  const { authToken } = useAuth();

  const { username, setUsername } = useState("Test");
  
  const { gardens, setGardens } = useState(exampleGardens());
  
 
  useEffect(() => {
    if (authToken) {
     print(authToken)
    }
  }, [authToken]); 


  return (
    <div className='app' style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
      <NavBar username={username} />
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
          <Garden authToken={authToken } />
        </div>
      </DndProvider>
    </div>
  )
}

export default DashboardPage;