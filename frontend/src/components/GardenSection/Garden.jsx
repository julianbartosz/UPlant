import React, { useRef, useEffect, useState, useContext } from 'react';
import './Garden.css';
import { useDrop } from 'react-dnd';
import { FaPlus } from 'react-icons/fa';
import { useUser } from '../../contexts/ProtectedRoute';
import { Tooltip } from 'react-tooltip';



const Garden = () => {

    const accept = 'PLANT';
    const containerRef = useRef(null);
    const [fontSize, setFontSize] = useState(40); // Default font size
    const [selectedGardenIndex, setSelectedGardenIndex] = useState(0); // Track selected garden
    const { gardens, handleAddGarden, handleDeleteGarden, handleUpdateGarden, adjustCellRowTop, adjustCellRowBottom } = useUser(); // Get gardens and functions from context
    const [selectedCells, setSelectedCells] = useState(new Set());

    const selectedCellsRef = useRef(selectedCells); // Store the selected cells in a ref to prevent state lag
    const selectedGardenIndexRef = useRef(selectedGardenIndex); // Store the selected garden index in a ref to prevent state lag

    //  ref with state
    useEffect(() => {
        selectedCellsRef.current = selectedCells;
    }, [selectedCells]);

    useEffect(() => {
        selectedGardenIndexRef.current = selectedGardenIndex;
    }, [selectedGardenIndex]);

    const handleCellClick = (i, j) => {

        console.log(`Cell clicked at (${i}, ${j})`);
        console.log("Current selected cells: ", selectedCells);

        const newSet = new Set(selectedCells); // Create a copy of the current selected cells
        const key = `${i}-${j}`;

        if (newSet.has(key)) {
            newSet.delete(key); 
        } else {
            newSet.add(key); 
        }
    
        setSelectedCells(newSet);
    };

    useEffect(() => {
        const updateFontSize = () => {

            if (containerRef.current) {

                const containerWidth = containerRef.current.offsetWidth;
                const containerHeight = containerRef.current.offsetHeight;

                // Dynamically calculate font size
                const calculatedFontSize = Math.min(
                    containerWidth / gardens[selectedGardenIndex].x,
                    containerHeight / gardens[selectedGardenIndex].y
                ) * 0.5;
                setFontSize(calculatedFontSize);
            }
        };

        // Call initially and add a resize event listener
        updateFontSize();
        window.addEventListener('resize', updateFontSize);

        return () => window.removeEventListener('resize', updateFontSize);
    }, [gardens, selectedGardenIndex]);

    const DropTarget = (obj, i, j) => {
        const [, drop] = useDrop(() => ({
            accept,
            drop: (item) => {

                console.log('Selected cells before drop:', selectedCellsRef.current); // Log the selected cells
                console.log('Dropped item:', item, 'into selected cells');

                const newCells = [...gardens[selectedGardenIndexRef.current].cells]; // Deep copy the garden cells
                
                // Iterate through selected cells
                selectedCellsRef.current.forEach(key => {
                    console.log("Selected cell key:", key);
                    const [row, col] = key.split('-').map(Number);
                    console.log(`Selected cell: (${row}, ${col})`);
                    
                    // Ensure row and col are within grid boundaries
                    if (row < gardens[selectedGardenIndexRef.current].y && col < gardens[selectedGardenIndexRef.current].x) {
                        console.log("Putting item in cell", row, col);
                        // Update the selected cell with the dropped item
                        newCells[row][col] = item;
                    } else {
                        console.error(`Invalid drop position: (${row}, ${col})`);
                    }
                });

                console.log("NEW CELLS", newCells);

                // Update the garden with new cells
                const updatedGarden = {
                    ...gardens[selectedGardenIndexRef.current], // Copy current garden state
                    cells: newCells // Assign new cells with updated values
                };

                console.log('Updated garden:', updatedGarden);

                // Clear selected cells after drop
                setSelectedCells(new Set());
                handleUpdateGarden(updatedGarden);

                console.log(gardens);
            },
        }));

        // Add click handler to toggle selection
        const isSelected = selectedCells.has(`${i}-${j}`);
        const cellClickHandler = () => handleCellClick(i, j);
    
      
        return (
        <div
        key={`${i}-${j}`}
        ref={drop}
        className={`square ${isSelected ? 'selected' : ''}`}
        style={{ fontSize: `${fontSize}px` }}
        onClick={cellClickHandler} // Add click handler here
        title={obj ? obj.name : "Name"} // Add tooltip with obj.name
        >
            
        {obj ? obj.icon : ""}
        </div>
        )
    };

    useEffect(() => {

        const observer = new MutationObserver(() => {
            setFontSize((prevFontSize) => prevFontSize + 0); // Trigger re-render
        });

        if (containerRef.current) {
            observer.observe(containerRef.current, { childList: true, subtree: true });
        }

        return () => {
            if (containerRef.current) {
            observer.disconnect();
            }
        };

    }, []);
    

    const handleGridSizeChange = (direction, change, edge) => {
        const newGarden = { ...gardens[selectedGardenIndex] }; // Copy current garden state

        // Ensure dimensions are within bounds
        if ((direction === 'x' && newGarden.x + change < 1) || (direction === 'y' && newGarden.y + change < 1)) {
            alert("Grid size cannot be less than 1.");
            return;
        }

        if (direction === 'x') {
            if (edge === 'left') {
                newGarden.cells.forEach(row => {
                    if (change > 0) {
                        row.unshift(null); // Add column to the left
                    } else {
                        row.shift(); // Remove column from the left
                    }
                });
            } else if (edge === 'right') {
                newGarden.cells.forEach(row => {
                    if (change > 0) {
                        row.push(null); // Add column to the right
                    } else {
                        row.pop(); // Remove column from the right
                    }
                });
            }
            newGarden.x += change;

        } else if (direction === 'y') {
            if (edge === 'top') {
                if (change > 0) {
                    newGarden.cells.unshift(Array(newGarden.x).fill(null)); // Add row to the top
                } else {
                    newGarden.cells.shift(); // Remove row from the top
                }
            } else if (edge === 'bottom') {
                if (change > 0) {
                    newGarden.cells.push(Array(newGarden.x).fill(null)); // Add row to the bottom
                } else {
                    newGarden.cells.pop(); // Remove row from the bottom
                }
            }
            newGarden.y += change;
        }

        // Update the garden with new dimensions
        handleUpdateGarden(newGarden);

    };
    // useEffect(() => {
    // Removed unused adjustGridSize function
    // useEffect(() => {
    //     const updateFontSize = () => {
    //         if (containerRef.current) {
    //             const containerWidth = containerRef.current.offsetWidth;
    //             const containerHeight = containerRef.current.offsetHeight;
                
    //             // Dynamically calculate font size
    //             const calculatedFontSize = Math.min(containerWidth / gardens[selectedGardenIndex].x, containerHeight / gardens[selectedGardenIndex].y) * 0.5;
    //             setFontSize(calculatedFontSize);
    //         }
    //     };

    //     // Call initially and add a resize event listener
    //     updateFontSize();
    //     window.addEventListener('resize', updateFontSize);

    //     return () => window.removeEventListener('resize', updateFontSize);
    // }, [gardens[selectedGardenIndex].x, gardens[selectedGardenIndex].y]); // Recalculate when dimensions change
    
    
    const createGrid = () => {
        
        return gardens[selectedGardenIndex].cells.map((row, i) => (
            <div key={i} className="row">
                {row.map((item, j) => (
                    <div data-tooltip-id="my-tooltip" data-tooltip-content={item ? item.name : ""}>{DropTarget(item, i, j)}</div>
                ))}
            </div>
        ));
    };
  

    return (
        <div className="container" ref={containerRef}>

            <div style={{ position: "absolute", top: 0, left: 0}}>
            <GardenBar handleAddGarden={handleAddGarden} gardens={gardens} selectedGardenIndex={selectedGardenIndex} setSelectedGardenIndex={setSelectedGardenIndex}/>
            </div>

            <div className="garden" style={{ 
                display: "grid",
                gridTemplateRows: `repeat(${gardens[selectedGardenIndex].y}, 1fr)`,
                gridTemplateColumns: `repeat(${gardens[selectedGardenIndex].x}, 1fr)`,
            }}>

                {createGrid()}
                <Tooltip id="my-tooltip" />
                <div style={{ position: "absolute", top: "0", left: "50%", transform: "translateX(-50%)", zIndex: 1,  gap: "10px"}}>
            {/* Top Center Button */}
            <button className="add-remove-btn" onClick={() => adjustCellRowTop(gardens[selectedGardenIndexRef.current])}>+</button>
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('y', -1, "top")}>-</button>
        </div>

        <div style={{
            position: "absolute",
            top: "50%", left: "0", 
            transform: "translateY(-50%)",
            zIndex: 1,
            display: "flex",
            flexDirection: "column", // Stack buttons vertically
            justifyContent: "center",
            gap: "10px", // Space between buttons
        }}>
            {/* Left Center Button */}
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('x', -1, "left")}>-</button>
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('x', 1, "left")}>+</button>
        </div>

        <div style={{
            position: "absolute",
            top: "50%", right: "0",
            transform: "translateY(-50%)",
            zIndex: 1,
            display: "flex",
            flexDirection: "column", // Stack buttons vertically
            justifyContent: "center",
            gap: "10px", // Space between buttons
        }}>
            {/* Right Center Button */}
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('x', 1, "right")}>+</button>
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('x', -1, "right")}>-</button>
        </div>

        <div style={{ position: "absolute", bottom: "0", left: "50%", transform: "translateX(-50%)", zIndex: 1 }}>
            {/* Bottom Center Button */}
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('y', 1, "bottom")}>+</button>
            <button className="add-remove-btn" onClick={() => handleGridSizeChange('y', -1, "bottom")}>-</button>
        </div>
            </div>
        </div>
    );
};

const GardenBar = ({ handleAddGarden, gardens, selectedGardenIndex, setSelectedGardenIndex }) => {

    const btnstyle = {
        width: '120px',
        fontSize: "14px",
        borderColor: 'black'
    };    

    return (
        <div className="garden-bar">
            <div className='garden-bar-item' key={-1}>
                <button onClick={handleAddGarden} style={{borderRadius: "30px", height: "40px"}}>

                    <FaPlus style={{fontSize: "20px" }} />
                    </button>
                </div>

            {gardens.map((garden, index) => (
                <div className='garden-bar-item' key={index}>
                    <button 
                        style={{ 
                            ...btnstyle, 
                            backgroundColor: selectedGardenIndex === index ? 'green' : 'lightgreen' 
                        }}
                        onClick={() => setSelectedGardenIndex(index)}
                    >
                        {garden.name}
                    </button>
                </div>
            ))}
        </div>
    );
};

export default Garden;