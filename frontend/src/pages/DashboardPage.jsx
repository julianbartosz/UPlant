/**
 * @file DashboardPage.jsx
 * @version 1.0.0
 * @description Main dashboard interface for the garden planting application that 
 *              allows users to view, add, and remove plants from their gardens.
 * 
 * @details
 * This component provides the following functionality:
 * - Displays all user gardens and allows switching between them
 * - Provides a grid interface for visualizing garden layouts
 * - Supports adding plants to selected empty cells
 * - Enables removal of existing plants from selected cells
 * - Shows notifications relevant to the selected garden
 * - Provides navigation and settings access
 * - Allows creation of new gardens via a form interface
 * 
 * The dashboard is structured with the following layout:
 * - Navigation bar at the top
 * - Plant selection sidebar on the left
 * - Garden management controls
 * - Interactive garden grid in the center
 * - Notification panel on the right
 */
import { useEffect, useRef, useState } from 'react';
import { useContext } from 'react';
import { GardenGrid } from '../components/ui';
import { 
  NotificationSection, 
  GardenBar, 
  PlantSearchSideBar, 
  NavBar 
} from '../components/layout';
import { GridLoading } from '../components/widgets';
import { UserContext } from '../context/UserProvider';
import { GardenForm } from '../components/forms';
import { useContentSize } from '../hooks';
import { BASE_API, HOME_URL, DEBUG } from '../constants';
import './styles/dashboard-page.css';

/**
 * @function addPlantToGarden
 * @description Adds a plant to the garden via API call
 * @param {Object} plant 
 * @param {number} gardenId -
 * @param {string} coordinates 
 * @returns {Promise<Object>} 
 */
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

/**
 * @function removePlantFromGarden
 * @description Removes a plant from the garden via API call
 * @param {number} logId - The ID of the garden log to remove
 * @returns {Promise<boolean>} - Success indicator
 */
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

/**
 * @function DashboardPage
 * @description Main dashboard component that displays gardens and plants
 * @returns {JSX.Element} The rendered dashboard page
 */
function DashboardPage() {
  // Context and state
  const { gardens, dispatch, loading } = useContext(UserContext);
  const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
  const [selectedEmptyCells, setSelectedEmptyCells] = useState(new Set());
  const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());
  const [toggleForm, setToggleForm] = useState(false);
  const [gridLoading, setGridLoading] = useState(false);
  const [loadingEstimate, setLoadingEstimate] = useState(0);
  
  // Refs
  const containerRef = useRef(null);
  const previousLengthRef = useRef(null);
  
  // Hooks
  const contentSize = useContentSize(containerRef);

  /**
   * Track changes to gardens array length to update selected index when gardens are added/removed
   */
  useEffect(() => {
    if (!Array.isArray(gardens)) return;
    
    if (previousLengthRef.current === null) {
      previousLengthRef.current = gardens.length;
      return;
    }
    
    if (gardens.length < previousLengthRef.current.length) {
      DEBUG && console.log("A garden was removed!");
    } else if (gardens.length > previousLengthRef.current.length) {
      DEBUG && console.log("A garden was added!");
      setSelectedGardenIndex(0);
    }
    
    previousLengthRef.current = gardens;
  }, [gardens?.length]);
  
  /**
   * Reset selected cells when changing gardens
   */
  useEffect(() => {
    setSelectedEmptyCells(new Set());
    setSelectedPlantCells(new Set());
  }, [selectedGardenIndex]);

  /**
   * @function handleAddPlantsToGarden
   * @description Handles adding plants to selected empty cells
   * @param {Object} plant - The plant to add
   */
  const handleAddPlantsToGarden = async (plant) => {
    if (DEBUG) {
      console.log("--- Adding plant to garden ---");
      console.log("Plant:", plant);
      console.log("Selected Garden Index:", selectedGardenIndex);
    }
    
    if (gridLoading) return;
    
    setLoadingEstimate(selectedEmptyCells.size);
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
      
      dispatch({ 
        type: 'ADD_GARDEN_LOGS', 
        garden_index: selectedGardenIndex, 
        payload: gardenLogs 
      });
    } catch (error) {
      console.error("Failed to add plant to garden:", error);
      alert("Error: Please try again.");
    } finally {
      setGridLoading(false);
    }
  };

  /**
   * @function handleRemovePlantsFromGarden
   * @description Handles removing plants from selected cells
   */
  const handleRemovePlantsFromGarden = async () => {
    if (gridLoading) return;
    
    setLoadingEstimate(selectedPlantCells.size / 2.2);
    setGridLoading(true);
    
    const selectedCells = new Set(selectedPlantCells);  
    setSelectedPlantCells(new Set());

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
      dispatch({ 
        type: 'PATCH_CELLS', 
        garden_index: selectedGardenIndex, 
        payload: newCells 
      });
    } catch (error) {
      console.error("Error removing plants:", error);
      alert("Error: Please try again.");
    } finally {
      setGridLoading(false);
    }
  };

  /**
   * @function cellClickHandler
   * @description Handles cell click events in the garden grid
   * @param {Object|null} obj - The cell object or null if empty
   * @param {number} i - Row index
   * @param {number} j - Column index
   */
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

  // Loading state
  if (loading) return <GridLoading />;

  /**
   * @function toggleGardenForm
   * @description Toggle garden form visibility and reset selections
   */
  const toggleGardenForm = () => {
    setSelectedEmptyCells(new Set());
    setSelectedPlantCells(new Set());
    setToggleForm(!toggleForm);
  };

  return (
    <>
      <NavBar
        title="Dashboard"
        onBack={() => { window.location.href = HOME_URL; }}
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
          onAdd={toggleGardenForm}
        />
        
        {!loading && (
          <div 
            className="garden-grid-container" 
            style={{height: `${contentSize.height - 88}px`}}
          >
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
            ) : (
              <GardenForm 
                callback={() => {setToggleForm(false);}} 
              />
            )}
          </div>
        )}
        
        <div
          className="notification-section-container"
          style={{height: `${contentSize.height - 88}px`}}
        >
          <NotificationSection
            selectedGardenIndex={selectedGardenIndex}
          />
        </div>
      </div>
    </>
  );
}

export default DashboardPage;