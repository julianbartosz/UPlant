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
  
  useEffect(() => { selectedEmptyCellsRef.current = selectedEmptyCells; }, [selectedEmptyCells]);
  useEffect(() => { selectedPlantCellsRef.current = selectedPlantCells; }, [selectedPlantCells]);
  
  
  const handleAddPlantToGarden = (plant, y, x) => {
    const newGarden = { ...gardens[selectedGardenIndexRef.current] };
    const gardenId = newGarden.id;
    const rollback = { ...newGarden };
    
    if (DEBUG) {
        console.log("Adding plant to garden:", { 
          garden: newGarden, 
          index: selectedGardenIndexRef.current, 
          plant: plant, 
          planted_date: "2025-04-22",
          x: x, 
          y: y 
        });
    }

    // Validate inputs
    if (!newGarden) {
        console.error("Invalid garden index:", selectedGardenIndexRef.current);
        alert("Error: Please try again.");
        return;
    }

    if (newGarden.cells[y][x] !== null) {
        console.error("Cell is already occupied:", { x: x, y: y });
        alert("Error: Please try again.");
        return;
    }

    if (plant.type !== 'SHEAR' && (plant.id === undefined || typeof plant.id !== 'number')) {
        console.error("Invalid plant data:", plant);
        alert("Error: Invalid plant data.");
        return;
    }

    newGarden.cells[y][x] = plant;

    // Optimistically update UI
    dispatch({ type: 'UPDATE_GARDEN', garden_index: selectedGardenIndexRef.current, payload: newGarden }); 

    const reqBody =  { notes: "EMPTY", health_status: "Healthy", garden: gardenId, plant: plant.id, x_coordinate: x, y_coordinate: y };

    if (DEBUG) {
      console.log("Request body:", reqBody);
    }

    // IIFE to handle async operation
    (async () => {
        try {
            const response = await fetch(`${BASE_API}/api/gardens/garden-logs/`, {
                method: 'POST',
                // credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token 4c1775be909a3873ee6c23104d433adaf4cbde29`,
                },
                body: JSON.stringify({ 
                    ...reqBody,
                    planted_date: "2025-04-22",
                }),
            });

            if (!response.ok) {
                if (DEBUG) {
                  console.error("Failed to add plant to garden:", response);
                } else {
                  console.error("Failed to add plant to garden:", response.statusText);
                }
                // Rollback UI
                dispatch({ type: 'UPDATE_GARDEN', garden_index: selectedGardenIndexRef.current, payload: rollback });
                alert("Error: Please try again.");
                return;
            }
            console.log("Success");
    
        } catch (error) {
            console.error("Failed to add plant to garden:", error);
            // Rollback UI
            dispatch({ type: 'UPDATE_GARDEN', garden_index: gardenIndex, payload: rollback });
            alert("Error: Please try again.");
        }
    })(); 
}

const handleRemovePlantFromGarden = (y, x) => {
    const newGarden = { ...gardens[selectedGardenIndexRef.current] };
    const rollback = { ...newGarden };
    const plant = newGarden.cells[y][x];
    if (DEBUG) {
        console.log("Removing plant from garden:", {
          garden: newGarden,
          index: selectedGardenIndexRef.current,
          plant: plant,
          x: x,
          y: y
        });
    }
    if (!newGarden) {
        console.error("Invalid garden index:", selectedGardenIndexRef.current);
        alert("Error: Please try again.");
        return;
    }
    console.log("NEW GARDEN: ", newGarden);
    const logId = newGarden.cells[y][x].logId;
    if (newGarden.cells[y][x] === null) {
        console.error("Cell is already empty:", { x: x, y: y });
        alert("Error: Please try again.");
        return;
    }
    
    newGarden.cells[y][x] = null;

    // Optimistically update UI
    dispatch({ type: 'UPDATE_GARDEN', garden_index: selectedGardenIndexRef.current, payload: newGarden });

    // IIFE to handle async operation
    (async () => {
        try {
            const response = await fetch(`${BASE_API}/api/gardens/garden-logs/${logId}/`, {
                method: 'DELETE',
                // credentials: 'include',
                headers: {
                    'Authorization': `Token 4c1775be909a3873ee6c23104d433adaf4cbde29`,
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                if (DEBUG) {
                  console.error("Failed to remove plant from garden:", response);
                } else {
                  console.error("Failed to remove plant from garden:", response.statusText);
                }
                // Rollback UI
                dispatch({ type: 'UPDATE_GARDEN', garden_index: selectedGardenIndexRef.current, payload: rollback });
                alert("Error: Please try again.");
                return;
            }

            console.log("Success");

        } catch (error) {
            console.error("Error updating gardens:", error);
            // Rollback UI
            dispatch({ type: 'UPDATE_GARDEN', garden_index: selectedGardenIndexRef.current, payload: rollback });
            alert("Error: Please try again.");
        }
    })();
}


  if (loading) {
    return <GridLoading />;
  }
  const handlePlantClick = (item) => {
    if (item.type === 'SHEAR') {
      selectedPlantCellsRef.current.forEach(key => {
        const [row, col] = key.split('-').map(Number);
        if (row < gardens[selectedGardenIndexRef.current].size_y && col < gardens[selectedGardenIndexRef.current].size_x) handleRemovePlantFromGarden(row, col);
      });
      return;
    }
    

    const currentGarden = gardens[selectedGardenIndexRef.current]
      selectedEmptyCellsRef.current.forEach(key => {
        const [row, col] = key.split('-').map(Number);
        console.log("ROW COL: ", row, col);
        if (row < currentGarden.size_y && col < currentGarden.size_x) handleAddPlantToGarden(item, row, col);
      });
  };

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
        onPlantClick={handlePlantClick}
        onShearClick={() => { handlePlantClick({ type: 'SHEAR' }); }}
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
          />

          ) : <GardenForm callback={() => {setToggleForm(false);}} />}
          </div>
          }
          

          <div
            className="garden-notification-container"
            style={{
              borderTop: '2px solid black',
              alignSelf: 'end',
              height: `${contentSize.height - 88}px`,
            }}
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
