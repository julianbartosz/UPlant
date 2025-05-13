/**
 * @file GardenGrid.jsx
 * @version 1.1.0
 * @description Interactive garden grid component for visualizing and managing plants in a garden.
 * 
 * @details
 * The GardenGrid component displays a interactive grid representing a garden layout.
 * It allows users to:
 * - View plants placed in the garden with appropriate icons
 * - Select empty cells for adding plants
 * - Select plant cells for removal
 * - Resize the garden (expand/contract) in all four directions
 * - View loading states during garden operations
 * 
 * The garden cells use a consistent styling pattern and highlight selected cells appropriately.
 * Tooltips display plant names on hover for better usability.
 * The garden size can be dynamically adjusted, with validation to prevent destruction of placed plants.
 */
import { ICONS } from "../../constants";
import { 
  FaArrowUp, 
  FaArrowDown, 
  FaArrowLeft, 
  FaArrowRight 
} from "react-icons/fa";
import { CircleButton } from "../buttons";
import { Tooltip } from "react-tooltip";
import "./styles/garden-grid.css";
import { useContext, useState, useEffect } from "react";
import { UserContext } from "../../context/UserProvider";
import { MAXSIZE_GARDEN, BASE_API, DEBUG } from "../../constants";
import { LoadingBar } from "../widgets";

/**
 * Updates garden dimensions in the backend
 * 
 * @param {Object} garden - Garden object with updated dimensions
 * @returns {Promise<Response>} - API response
 * @throws {Error} - If the API request fails
 */
const updateGardenSize = async (garden) => {
  const response = await fetch(`${BASE_API}/gardens/gardens/${garden.id}/`, {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ size_x: garden.size_x, size_y: garden.size_y }),
  });

  if (!response.ok) {
    throw new Error("Failed to update garden dimensions");
  }
  return response;
};

/**
 * Garden grid component for displaying and interacting with garden cells
 * 
 * @component
 * @param {Object} props - Component props
 * @param {number} props.selectedGardenIndex - Index of the currently selected garden
 * @param {Object} props.contentSize - Dimensions of the container (width, height)
 * @param {boolean} [props.interactive=true] - Whether the grid supports interaction
 * @param {Set} [props.selectedEmptyCells=null] - Set of empty cells that are selected
 * @param {Set} [props.selectedPlantCells=null] - Set of plant cells that are selected
 * @param {Function} [props.cellClickHandler=null] - Handler for cell click events
 * @param {Set} [props.coloredCells=null] - Set of cells to highlight as needing attention
 * @param {boolean} props.loading - Whether the grid is in a loading state
 * @param {number} props.loadingEstimate - Estimated loading time in seconds
 * @returns {JSX.Element} - Rendered component
 */
const GardenGrid = ({
  selectedGardenIndex, 
  contentSize,
  interactive = true,
  selectedEmptyCells = null, 
  selectedPlantCells = null,
  cellClickHandler = null,
  coloredCells = null,
  loading,
  loadingEstimate
}) => {
  const [view, setView] = useState(0);
  const context = useContext(UserContext);

  if (context === undefined) {
    throw new Error("GardenGrid must be used within a UserProvider");
  }
  
  const { gardens, dispatch, loading: ggLoading } = context;
  
  if (DEBUG) {
    console.log("Gardens:", gardens);
    console.log("Selected Garden Index:", selectedGardenIndex);
    console.log("Dispatch:", dispatch);
  }
  
  if (ggLoading || dispatch === undefined || dispatch === null) {  
    return null;
  }

  // Update view size when content dimensions change
  useEffect(() => {
    if (!contentSize) return;
    
    const { width, height } = contentSize;
    
    if (DEBUG) {
      console.log("Width:", width, "Height:", height);
    }
    
    setView(height - 88);
  }, [contentSize, selectedGardenIndex, gardens]);

  /**
   * Calculate the size of each grid cell based on container dimensions and garden size
   * @returns {number} - Size of each square cell in pixels
   */
  const calcSquareSize = () => {
    const { width, height } = contentSize;
    
    if (DEBUG) {
      console.log("Width:", width, "Height:", height);
    }
    
    const garden = gardens[selectedGardenIndex];
    const maxDimension = Math.max(garden.size_x, garden.size_y);
    const viewSize = Math.min(width * 0.6, height * 0.6);
    return viewSize / maxDimension;
  };
  
  const squareSize = calcSquareSize();
  const gridSize = { 
    width: gardens[selectedGardenIndex].size_x, 
    height: gardens[selectedGardenIndex].size_y 
  };

  // Cell selection helper functions
  const isSelectedEmpty = (i, j) => selectedEmptyCells && selectedEmptyCells.has(`${i}-${j}`);
  const isSelectedPlant = (i, j) => selectedPlantCells && selectedPlantCells.has(`${i}-${j}`);
  const isColored = (i, j) => coloredCells && coloredCells.has(`${i}-${j}`);

  /**
   * Handle garden grid resizing in all directions
   * 
   * @param {number} change - Amount to change the size (+1 to expand, -1 to contract)
   * @param {string} edge - Which edge to modify ('left', 'right', 'top', 'bottom')
   * @param {number} gardenIndex - Index of the garden to modify
   */
  const handleGridResizing = (change, edge, gardenIndex) => {
    const rollBack = { ...gardens[gardenIndex] };
    const newGarden = { ...gardens[gardenIndex] };
    
    if (edge === 'left' || edge === 'right') {
      // Handle horizontal resizing
      if (newGarden.size_x + change > MAXSIZE_GARDEN) {
        alert(`Cannot resize: Maximum garden width of ${MAXSIZE_GARDEN} reached.`);
        return;
      }

      if (newGarden.size_x + change < 1) {
        alert('Cannot resize: Garden width cannot be smaller than 1.');
        return;
      }

      if (change < 0) {
        const columnIndex = edge === 'left' ? 0 : newGarden.size_x - 1;
        const hasPlant = newGarden.cells.some(row => row[columnIndex] !== null);
        
        if (hasPlant) {
          alert('Cannot resize: Plants would be deleted.');
          return;
        }
      }

      newGarden.size_x += change;
      if (edge === 'left') {
        newGarden.cells.forEach(row => change > 0 ? row.unshift(null) : row.shift());
      } else if (edge === 'right') {
        newGarden.cells.forEach(row => change > 0 ? row.push(null) : row.pop());
      }
    } else if (edge === 'top' || edge === 'bottom') {
      // Handle vertical resizing
      if (newGarden.size_y + change > MAXSIZE_GARDEN) {
        alert(`Cannot resize: Maximum garden height of ${MAXSIZE_GARDEN} reached.`);
        return;
      }

      if (newGarden.size_y + change < 1) {
        alert('Cannot resize: Garden height cannot be smaller than 1.');
        return;
      }

      if (change < 0) {
        const rowIndex = edge === 'top' ? 0 : newGarden.size_y - 1;
        
        if (DEBUG) {
          console.log("Row Index:", rowIndex);
          console.log("New Garden:", newGarden);
        }
        
        const hasPlant = newGarden.cells[rowIndex].some(cell => cell !== null);
        if (hasPlant) {
          alert('Cannot resize: Plants would be deleted.');
          return;
        }
      }

      newGarden.size_y += change;
      if (edge === 'top') {
        change > 0 ? newGarden.cells.unshift(Array(newGarden.size_x).fill(null)) : newGarden.cells.shift();
      } else if (edge === 'bottom') {
        change > 0 ? newGarden.cells.push(Array(newGarden.size_x).fill(null)) : newGarden.cells.pop();
      }
    }
    
    if (DEBUG) {
      console.log("Updating garden:", { 
        type: 'UPDATE_GARDEN', 
        garden_index: gardenIndex, 
        payload: newGarden 
      });
    }
    
    try {
      // Optimistic update
      dispatch({ type: 'UPDATE_GARDEN', garden_index: gardenIndex, payload: newGarden });
    } catch (error) {
      console.error("Error updating gardens:", error);
    }
    
    // IIFE to handle async operation
    (async () => {
      try {
        await updateGardenSize(newGarden);
      } catch (error) {
        console.error("Error updating gardens:", error);
        
        try {
          // Rollback to previous state
          dispatch({ type: 'UPDATE_GARDEN', garden_index: gardenIndex, payload: rollBack });
        } catch (error) {
          console.error("Error rolling back gardens:", error);
        }
        
        alert("Failed to update gardens. Please try again.");
      }
    })();
  };

  return (
    <>
      <div 
        className="grid-container" 
        style={{
          width: `${squareSize * gridSize.width}px`, 
          height: `${squareSize * gridSize.height}px`,
        }}
      >
        <div 
          className="grid" 
          style={{
            gridTemplateColumns: `repeat(${gridSize.width}, ${squareSize}px)`, 
            gridTemplateRows: `repeat(${gridSize.height}, ${squareSize}px)`,
          }}
        >
          {gardens[selectedGardenIndex].cells.map((row, i) => (
            row.map((item, j) => (
              <div 
                key={`${i}-${j}`} 
                data-tooltip-id="my-tooltip" 
                data-tooltip-content={item ? item.plant_detail.name : ""}
              >
                <div
                  className={`
                    ${isColored(i, j) ? 'needs-care' : 'square'} 
                    ${isSelectedEmpty(i, j) ? 'selected' : ''} 
                    ${isSelectedPlant(i, j) ? 'selected-shear' : ''}
                  `}
                  style={{ fontSize: `${squareSize/2}px` }}
                  onClick={() => { !loading && cellClickHandler && cellClickHandler(item, i, j) }}
                >
                  {item ? (ICONS[item.plant_detail.family] || ICONS['default']) : ""}
                </div>
              </div>
            ))
          ))}
          
          <Tooltip id="my-tooltip" style={{ zIndex: 9999 }} />
          
          {interactive && (
            <>
              {/* Right edge resize controls */}
              <div 
                style={{
                  position: "absolute",
                  top: "50%", 
                  right: "-20px",
                  transform: "translateY(-50%)",
                  zIndex: 2,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                }}
              >
                <CircleButton 
                  text={<FaArrowLeft />} 
                  className="grid-remove-btn" 
                  onClick={() => !loading && handleGridResizing(-1, "right", selectedGardenIndex)} 
                />
                <CircleButton 
                  text={<FaArrowRight />} 
                  className="grid-add-btn" 
                  onClick={() => !loading && handleGridResizing(1, "right", selectedGardenIndex)} 
                />
              </div>
              
              {/* Bottom edge resize controls */}
              <div 
                style={{ 
                  position: "absolute", 
                  bottom: "-20px", 
                  left: "50%", 
                  transform: "translateX(-50%)", 
                  zIndex: 2, 
                  display: "flex" 
                }}
              >
                <CircleButton 
                  text={<FaArrowDown />} 
                  className="grid-add-btn" 
                  onClick={() => !loading && handleGridResizing(1, "bottom", selectedGardenIndex)} 
                />
                <CircleButton 
                  text={<FaArrowUp />} 
                  className="grid-remove-btn" 
                  onClick={() => !loading && handleGridResizing(-1, "bottom", selectedGardenIndex)} 
                />
              </div>
            </>
          )}
          
          {/* Loading overlay */}
          {loading && (
            <div 
              style={{
                position: "absolute",
                top: "50%",
                transform: "translateY(-50%)",
                left: "0px",
                zIndex: 1,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                height: "100%",
                width: '100%',
                backgroundColor: 'rgba(192, 191, 191, 0.5)',
              }}
            >
              <LoadingBar 
                isLoading={loading} 
                seconds={loadingEstimate} 
                style={{width: 'calc(100% - 30px)'}} 
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default GardenGrid;