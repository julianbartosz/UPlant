import { ICONS } from "../../constants";
import { 
    FaArrowUp, 
    FaArrowDown, 
    FaArrowLeft, 
    FaArrowRight 
} from "react-icons/fa";
import { CircleButton } from "../buttons";
import { Tooltip } from "react-tooltip";
import { useGardens } from "../../hooks";
import "./styles/garden-grid.css"
import { useContext, useState, useEffect } from "react";
import { UserContext } from "../../context/UserProvider";
import { MAXSIZE_GARDEN } from "../../constants";

const GardenGrid = ({
    selectedGardenIndex, 
    contentSize,
    interactive = true,
    selectedEmptyCells = null, 
    selectedPlantCells = null,
    cellClickHandler = null,
    coloredCells = null
}) => {

    // const [squareSize, setSquareSize] = useState(0)
    const [view, setView] = useState(0);

    const context = useContext(UserContext);

    if (context === undefined) {
        throw new Error("GardenGrid must be used within a UserProvider");
    }
    const { gardens, dispatch, loading } = context;
    console.log("Gardens: ", gardens);
    console.log("Selected Garden Index: ", selectedGardenIndex);
    console.log("Dispatch: ", dispatch);
    
    if (loading || dispatch === undefined || dispatch === null) {  
        return null;
    }

    useEffect(() => {
        if (!contentSize) return;
        const { width, height } = contentSize;
        console.log("Width: ", width, "Height: ", height);
        const garden = gardens[selectedGardenIndex];
        const maxDimension = Math.max(garden.size_x, garden.size_y);
        const view = Math.min(width * 0.6, height * 0.6);
        setView(height - 88);
    }, [contentSize, selectedGardenIndex, gardens]);

    const calcSquareSize =  () =>{
        const { width, height } = contentSize;
        console.log("Width: ", width, "Height: ", height);
        const garden = gardens[selectedGardenIndex];
        const maxDimension = Math.max(garden.size_x, garden.size_y);
        const view = Math.min(width * 0.6, height * 0.6);
        return view / maxDimension;
}
    const squareSize = calcSquareSize();

    const gridSize = { width: gardens[selectedGardenIndex].size_x, height: gardens[selectedGardenIndex].size_y };

    const isSelectedEmpty = (i, j) => selectedEmptyCells && selectedEmptyCells.has(`${i}-${j}`);
    const isSelectedPlant = (i, j) => selectedPlantCells && selectedPlantCells.has(`${i}-${j}`);
    const isColored = (i, j) => coloredCells && coloredCells.has(`${i}-${j}`);

    const handleGridResizing = (change, edge, gardenIndex) => {
        const rollBack = { ...gardens[gardenIndex] };
        const newGarden = { ...gardens[gardenIndex] };
        
        if (edge === 'left' || edge === 'right') {
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
                console.log("Row Index: ", rowIndex);
                console.log("New Garden: ", newGarden);
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
        console.log("AAAAAA",{type: 'UPDATE_GARDEN', garden_index: gardenIndex, payload: newGarden})
        try {
            dispatch({type: 'UPDATE_GARDEN', garden_index: gardenIndex, payload: newGarden}) // Optimistic update
        } catch (error) {
            console.error("Error updating gardens:", error);
        }
        
        // IIFE to handle async operation
        (async () => {
            try {
                const response = await fetch(`${import.meta.env.VITE_GARDENS_API_URL}${newGarden.id}/`, {
                    method: 'PATCH',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    body: JSON.stringify({size_x: newGarden.size_x, size_y: newGarden.size_y}),
                });

                if (!response.ok) {
                    throw new Error("Failed to update gardens");
                }

            } catch (error) {
                console.error("Error updating gardens:", error);
                try {
                    dispatch({type: 'UPDATE_GARDEN', garden_index: gardenIndex, payload: rollBack}); // Rollback to previous state
                } catch (error) {
                    console.error("Error rolling back gardens:", error);
                }
                alert("Failed to update gardens. Please try again.");
            }
        })();
    } 
    
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
        }}>

    { gardens[selectedGardenIndex].cells.map((row, i) => (
                    row.map((item, j) => (
                        <div  key={`${i}-${j}`} data-tooltip-id="my-tooltip" data-tooltip-content={item ? item['common_name'] : ""}>
                            <div
                                className={`${isColored(i, j) ? 'needs-care' : 'square'} ${isSelectedEmpty(i, j) ? 'selected' : ''} ${isSelectedPlant(i, j) ? 'selected-shear' : ''}`}
                                style={{ 
                                    fontSize: `${squareSize/2}px`,
                                
                                }}
                                onClick={() => {cellClickHandler && cellClickHandler(item, i, j)}}
                            >
                                {item ? (ICONS[item.family] || ICONS['default']) : ""}
                            </div>
                        </div>
                    ))
                ))}

            <Tooltip id="my-tooltip" style={{ zIndex: 9999 }}/>
            {interactive && (
                <>
                   
                    <div style={{
                        position: "absolute",
                        top: "50%", right: "-20px",
                        transform: "translateY(-50%)",
                        zIndex: 1,
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                    }}>
                        {/* Right Center Button */}
                        <CircleButton text={<FaArrowLeft />} className="grid-remove-btn" onClick={() => handleGridResizing(-1, "right", selectedGardenIndex)} />
                        <CircleButton text={<FaArrowRight />} className="grid-add-btn" onClick={() => handleGridResizing(1, "right", selectedGardenIndex)} />
                    </div>
                    <div style={{ position: "absolute", bottom: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: 1, display: "flex" }}>
                        {/* Bottom Center Button */}
                        <CircleButton text={<FaArrowDown />} className="grid-add-btn" onClick={() => handleGridResizing(1, "bottom", selectedGardenIndex)} />
                        <CircleButton text={<FaArrowUp />} className="grid-remove-btn" onClick={() => handleGridResizing(-1, "bottom", selectedGardenIndex)} />
                    </div>
                </>
            )}
                
                
                    </div>
            
                </div>
        </>

    )
}

export default GardenGrid;

