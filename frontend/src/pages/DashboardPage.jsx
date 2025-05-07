import { useRef, useEffect, useState } from 'react';
import { useGardens, useUser } from '../hooks';
import { GardenGrid } from '../components/ui';
import { NotificationSection, GardenBar, PlantSearchSideBar, NavBar } from '../components/layout';
import { GridLoading } from '../components/widgets';
import { UserContext } from '../context/UserProvider';
import { useContext } from 'react';
import { GardenForm } from '../components/forms';
import { useContentSize } from '../hooks';
import { BASE_API, DEBUG } from '../constants';
import './styles/dashboard-page.css';

// Async function to add a plant to the garden
const addPlantToGarden = async (plant, gardenId, coordinates) => {
  const [y, x] = coordinates.split('-').map(Number);
  
  if (DEBUG) {
    console.log("Adding plant to garden:", { 
      plant: plant, 
      planted_date: new Date().toISOString().split('T')[0],
      x: x, 
      y: y 
    });
  }

  const reqBody = { 
    notes: "EMPTY", 
    health_status: "Healthy", 
    garden: gardenId, 
    plant: plant.id, 
    x_coordinate: x, 
    y_coordinate: y,
    planted_date: new Date().toISOString().split('T')[0]
  };

  if (DEBUG) {
    console.log("Request body:", reqBody);
  }

  const response = await fetch(`${BASE_API}/gardens/garden-logs/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(reqBody),
  });

  if (!response.ok) {
    throw new Error(`Failed to add plant: ${response.statusText}`);
  }

  return await response.json();
};

// Async function to remove a plant from the garden
const removePlantFromGarden = async (logId) => {
  if (DEBUG) {
    console.log("---Removing plant from garden---");
    console.log(`Log ID: ${logId}`);
  }

  const response = await fetch(`${BASE_API}/gardens/garden-logs/${logId}/`, {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to remove plant: ${response.statusText}`);
  }

  return true;
};

function DashboardPage() {
   
  const { gardens, dispatch, loading } = useContext(UserContext);
  const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
  const [selectedEmptyCells, setSelectedEmptyCells] = useState(new Set());
  const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());
  const [toggleForm, setToggleForm] = useState(false);
  
  const containerRef = useRef(null);
  const contentSize = useContentSize(containerRef);
  const selectedGardenIndexRef = useRef(selectedGardenIndex);
  const selectedEmptyCellsRef = useRef(selectedEmptyCells);
  const selectedPlantCellsRef = useRef(selectedPlantCells);

  const [gridLoading, setGridLoading] = useState(false);
  const [loadingEstimate, setLoadingEstimate] = useState(0);
  
  useEffect(() => { selectedEmptyCellsRef.current = selectedEmptyCells; }, [selectedEmptyCells]);
  useEffect(() => { selectedPlantCellsRef.current = selectedPlantCells; }, [selectedPlantCells]);
  
  const handleAddPlantsToGarden = async (plant) => {
    if (DEBUG) {
      console.log("--- Adding plant to garden ---");
      console.log("Plant:", plant);
      console.log("Selected Garden Index:", selectedGardenIndex);
    }
    
    if (gridLoading) return;
    setLoadingEstimate(selectedEmptyCells.size/1.2);
    const selectedCells = new Set(selectedEmptyCells);
    setSelectedEmptyCells(new Set());
    setGridLoading(true);
    
    const gardenId = gardens[selectedGardenIndex].id;
    let gardenLogs = [];

    try {
      for (let coordinates of selectedCells) {
        const data = await addPlantToGarden(plant, gardenId, coordinates);
        if (data) {
          gardenLogs.push(data);
        }
      }
      
      dispatch({ type: 'ADD_GARDEN_LOGS', garden_index: selectedGardenIndex, payload: gardenLogs });
    } catch (error) {
      console.error("Failed to add plant to garden:", error);
      alert("Error: Please try again.");
    } finally {
      setGridLoading(false);
    }
  };

  const handleRemovePlantsFromGarden = async () => {
    if (gridLoading) return;
    setLoadingEstimate(selectedPlantCells.size/2.2);
    setGridLoading(true);
    setSelectedPlantCells(new Set());
    const selectedCells = new Set(selectedPlantCells);  

    const newCells = gardens[selectedGardenIndex].cells.map((row, rowIndex) =>
      row.map((cell, colIndex) => {
        const key = `${rowIndex}-${colIndex}`;
        return selectedPlantCells.has(key) ? null : cell;
      })
    );

    try {
      for (let coordinates of selectedCells) {
        const [y, x] = coordinates.split('-').map(Number);
        const logId = gardens[selectedGardenIndex].cells[y][x].id;
        await removePlantFromGarden(logId);
      }

      console.log("All plants removed successfully");
      dispatch({ type: 'PATCH_CELLS', garden_index: selectedGardenIndex, payload: newCells });
    } catch (error) {
      console.error("Error removing plants:", error);
      alert("Error: Please try again.");
    } finally {
      setGridLoading(false);
    }
  };

  if (loading) {
    return <GridLoading />;
  }

  const cellClickHandler = (obj, i, j) => {
    const isTaken = obj !== null;
    const key = `${i}-${j}`;

    if (!isTaken) {
      const newSet = new Set(selectedEmptyCells);
      newSet.has(key) ? newSet.delete(key) : newSet.add(key);
      setSelectedEmptyCells(newSet);
    } else {
      const newSet = new Set(selectedPlantCells);
      newSet.has(key) ? newSet.delete(key) : newSet.add(key);
      setSelectedPlantCells(newSet);
    }
  };

  if (!gardens) return <GridLoading />;

  return (
    <>
      <NavBar
        title="Dashboard"
        buttonOptions={['back', 'settings', 'bell']}
        onBack={() => { window.location.href = import.meta.env.VITE_BACKEND_URL; }}
      />
      
      <PlantSearchSideBar
        page="dashboard"
        onPlantClick={handleAddPlantsToGarden}
        onShearClick={handleRemovePlantsFromGarden}
      />
        <div className="dashboard-content" ref={containerRef}>
            <GardenBar
              selectedGardenIndex={selectedGardenIndex}
              setSelectedGardenIndex={setSelectedGardenIndex}
              onAdd={() => { setToggleForm(!toggleForm); }}
            />
            
            
            
          {!loading && 
          <div className={ "garden-grid-container" } style={{height: `${contentSize.height-88}px`}}>
    
          {!toggleForm ? (
        <GardenGrid
            selectedGardenIndex={selectedGardenIndex}
            contentSize={contentSize}
            selectedEmptyCells={selectedEmptyCells}
            selectedPlantCells={selectedPlantCells}
            cellClickHandler={cellClickHandler}
            loading={gridLoading}
            loadingEstimate={loadingEstimate}
          />
          ) : <GardenForm callback={() => {setToggleForm(false);}} />}
          </div>
          }
          <div
            className="notification-section-container"
            style={{height: `${contentSize.height - 88}px`}}
          >
          <NotificationSection
            contentSize={contentSize}
            selectedGardenIndex={selectedGardenIndex}
          />
          
        </div>
    </div>
    </>
  );
}

export default DashboardPage;
