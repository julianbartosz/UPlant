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
import LoadingBarModal from '../components/modals/LoadingBarModal';
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

  const [gridLoading, setGridLoading] = useState(false);
  const [loadingEstimate, setLoadingEstimate] = useState(0);
  
  useEffect(() => { selectedEmptyCellsRef.current = selectedEmptyCells; }, [selectedEmptyCells]);
  useEffect(() => { selectedPlantCellsRef.current = selectedPlantCells; }, [selectedPlantCells]);
  
  const handleAddPlantsToGarden = async (plant) => {
    if (gridLoading) return;
    setLoadingEstimate(selectedEmptyCellsRef.current.size/2.2)
     const selectedCells = new Set(selectedEmptyCellsRef.current);
     setSelectedEmptyCells(new Set());
     setGridLoading(true);
      const gardenId = gardens[selectedGardenIndexRef.current].id;

      let gardenLogs = [];

        for (let coordinates of selectedCells) {
                const [y, x] = coordinates.split('-').map(Number);

                if (DEBUG) {
                  console.log("Adding plant to garden:", { 
                    index: selectedGardenIndexRef.current, 
                    plant: plant, 
                    planted_date: new Date().toISOString().split('T')[0], // Current date in YYYY-MM-DD format
                    x: x, 
                    y: y 
                  });
              }

                const reqBody =  { notes: "EMPTY", health_status: "Healthy", garden: gardenId, plant: plant.id, x_coordinate: x, y_coordinate: y };
                if (DEBUG) {
                  console.log("Request body:", reqBody);
                }
          
                let data;

                try {
                    const response = await fetch(`${BASE_API}/gardens/garden-logs/`, {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                            // 'Authorization': `Token 4c1775be909a3873ee6c23104d433adaf4cbde29`,
                        },
                        body: JSON.stringify({ 
                            ...reqBody,
                            planted_date: new Date().toISOString().split('T')[0],
                        }),
                    });

                    if (!response.ok) {
                        if (DEBUG) {
                          console.error("Failed to add plant to garden:", response);
                        } else {
                          console.error("Failed to add plant to garden:", response.statusText);
                        }
                        setGridLoading(false);
                        alert("Error: Please try again.");
                        return;
                    }

                    data = await response.json();
                    console.log("Response Data:", data);
                    console.log("Success");
                    // Wait for data before dispatching
                  if (data) {
                    console.log("Data:", data);
                    gardenLogs.push(data);
                  } else {
                    console.log('No data received from the server');
                  }

            
                } catch (error) {
                    console.error("Failed to add plant to garden:", error);
                    setGridLoading(false);
                    alert("Error: Please try again.");
                }
              }
              dispatch({ type: 'ADD_GARDEN_LOGS', garden_index: selectedGardenIndexRef.current, payload: gardenLogs });
              setGridLoading(false);
            }

const handleRemovePlantsFromGarden = async () => {
  if (gridLoading) return;
  setLoadingEstimate(selectedPlantCellsRef.current.size/2.2)
  setGridLoading(true);
  setSelectedPlantCells(new Set());
  const selectedCells = new Set(selectedPlantCellsRef.current);
  
  const newCells = gardens[selectedGardenIndexRef.current].cells.map((row, rowIndex) =>
    row.map((cell, colIndex) => {
      const key = `${rowIndex}-${colIndex}`;
      return selectedPlantCellsRef.current.has(key) ? null : cell;
    })
  );

  for (let coordinates of selectedCells) {
      const [y, x] = coordinates.split('-').map(Number);
      const logId = gardens[selectedGardenIndexRef.current].cells[y][x].id;

      if (DEBUG) {
        console.log("---Removing plant from garden---");
        console.log(`Selected Plant Cell: (${x}, ${y})`);
      }
      
      try {
        
          const response = await fetch(`${BASE_API}/gardens/garden-logs/${logId}/`, {
              method: 'DELETE',
              credentials: 'include',
              headers: {
                  'Content-Type': 'application/json',
              }
          });

          if (!response.ok) {
              setGridLoading(false);  

              if (DEBUG) {
                console.error("Failed to remove plant from garden:", response);
              } else {
                console.error("Failed to remove plant from garden:", response.statusText);
              }
               
              alert("Error: Please try again.");
              return;
          }
          console.log("Success");

      } catch (error) {
          setGridLoading(false);
          console.error("Error updating gardens:", error);
          alert("Error: Please try again.");
      }
   } 

   console.log("All plants removed successfully");
   dispatch({ type: 'PATCH_CELLS', garden_index: selectedGardenIndexRef.current, payload: newCells });
   setGridLoading(false);
}

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
     <LoadingBarModal loading={gridLoading} loadingEstimate={loadingEstimate} />
    </>
  );
}

export default DashboardPage;
