// frontend/src/components/GardenSection/Garden.jsx

import React, { useRef, useEffect, useState, useContext, lazy } from 'react';

import './Garden.css';
import { useDrop } from 'react-dnd';
import { FaPlus } from 'react-icons/fa';
import { MdDeleteForever } from "react-icons/md";
import { TbHttpDelete } from "react-icons/tb";
import plantFamilyIcons from '../../constants/icons'

import { TiDelete } from "react-icons/ti";
import { useGardens } from '../../contexts/ProtectedRoute';
import { Tooltip } from 'react-tooltip';


const Garden = () => {

    const accept = 'PLANT';

    const { 
        gardens, 
        handleUpdateGarden, 
        setGardens 
    } = useGardens(); 

    const [squareSize, setSquareSize] = useState(0);
    const [fontSize, setFontSize] = useState(null); 
    const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
    const [selectedCells, setSelectedCells] = useState(new Set());

    const containerRef = useRef(null);
    const selectedCellsRef = useRef(selectedCells);
    const selectedGardenIndexRef = useRef(selectedGardenIndex); 

    useEffect(() => {
        selectedCellsRef.current = selectedCells;
    }, [selectedCells]);

    useEffect(() => {
        selectedGardenIndexRef.current = selectedGardenIndex;
        setSelectedCells(new Set()); 

        const handleResize = () => {
            if (containerRef.current) {
                const { width, height } = containerRef.current.getBoundingClientRect();
                const maxDimension = Math.max(gardens[selectedGardenIndex].x, gardens[selectedGardenIndex].y);
                const newSquareSize = Math.min(width * 0.6, height * 0.6) / maxDimension;
                console.log("Old square size:", squareSize);
                setFontSize(newSquareSize * 0.3);
                setSquareSize(newSquareSize);

                console.log("New square size:", newSquareSize);
                
            }
        };

        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);

    }, [selectedGardenIndex, gardens]);


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
    

    const mediateGridSizeChange = (direction, change, edge) => {

        const newGarden = { ...gardens[selectedGardenIndex] };

        if (direction === 'x') {
            newGarden.x += change;
            if (edge === 'left') {
                newGarden.cells.forEach(row => change > 0 ? row.unshift(null) : row.shift());
            } else if (edge === 'right') {
                newGarden.cells.forEach(row => change > 0 ? row.push(null) : row.pop());
            }
            
        } else if (direction === 'y') {
            newGarden.y += change;
            if (edge === 'top') {
                change > 0 ? newGarden.cells.unshift(Array(newGarden.x).fill(null)) : newGarden.cells.shift();
            } else if (edge === 'bottom') {
                change > 0 ? newGarden.cells.push(Array(newGarden.x).fill(null)) : newGarden.cells.pop();
            }
        }
        
        handleUpdateGarden(newGarden, false);
    };



    const DropTarget = (obj, i, j) => {

        const handleCellClick = (i, j) => {
            const newSet = new Set(selectedCells); 
            const key = `${i}-${j}`;
    
            if (newSet.has(key)) {
                newSet.delete(key); 
            } else {
                newSet.add(key); 
            }
        
            setSelectedCells(newSet);
        };
        
        const isTaken = obj !== null;
        const isSelected = selectedCells.has(`${i}-${j}`);

        const cellClickHandler = () => { 
            if (isTaken) return;
            handleCellClick(i, j);
        }

        return (
        <div
        key={`${i}-${j}`}
        className={`square ${isSelected ? 'selected' : ''}`}
        style={{ fontSize: `${fontSize}px` }}
        onClick={cellClickHandler} 
        >
            {obj ? (plantFamilyIcons[obj.family] || plantFamilyIcons['default']) : ""}
        </div>
        )
    };

    const [, drop] = useDrop(() => ({
        accept,
        drop: (item) => {
            setGardens((prevGardens) => {
        
                const currentGarden = { ...prevGardens[selectedGardenIndexRef.current] };
                if (!currentGarden) {
                    console.error("Garden not found at index:", selectedGardenIndexRef.current);
                    return prevGardens;
                }

                const newCells = [...currentGarden.cells];

                selectedCellsRef.current.forEach(key => {
                    const [row, col] = key.split('-').map(Number);
                    if (row < currentGarden.y && col < currentGarden.x) {
                        console.log("Putting item in cell", row, col);
                        newCells[row][col] = item;
                    } else {
                        console.error(`Invalid drop position: (${row}, ${col})`);
                    }
                });

                const updatedGarden = {
                    ...currentGarden, 
                    cells: newCells 
                };
    
                console.log('Updated garden:', updatedGarden);
    
                const updatedGardens = [...prevGardens];
                updatedGardens[selectedGardenIndexRef.current] = updatedGarden;
    
                return updatedGardens;
            });
        },
    }));
  
    return (
        <div className="container" ref={containerRef}>
            <div style={{ position: "absolute", top: 0, left: 0 }}>
                <GardenBar selectedGardenIndex={selectedGardenIndex} setSelectedGardenIndex={setSelectedGardenIndex} />
            </div>
            <div 
                className="garden" 
                ref={drop} 
                style={{
                    gap: "2px",
                    border: "2px solid black",
                    margin: "10px 0",
                    width: `${squareSize * gardens[selectedGardenIndex].x}px`, 
                    height: `${squareSize * gardens[selectedGardenIndex].y}px`,
                    position: "relative",
                }}
            >
                <div 
                className="grid" 
                ref={drop} 
                style={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${gardens[selectedGardenIndex].x}, ${squareSize}px)`, 
                    gridTemplateRows: `repeat(${gardens[selectedGardenIndex].y}, ${squareSize}px)`,
                }}
            >
            
            {gardens[selectedGardenIndex].cells.map((row, i) => (
                row.map((item, j) => (
                    <div data-tooltip-id="my-tooltip" data-tooltip-content={item ? item['common_name'] : ""}>{DropTarget(item, i, j)}</div>
                ))
            ))}
                    </div>
                <Tooltip id="my-tooltip" style={{ zIndex: 9999 }}/>
                <div style={{ position: "absolute", top: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: -0.5 }}>
                    {/* Top Center Button */}
                    <button className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "top")}></button>
                    <button className="grid-remove-btn"  onClick={() => mediateGridSizeChange('y', -1, "top")}></button>
                </div>
                <div style={{
                    position: "absolute",
                    top: "50%", left: "-20px", 
                    transform: "translateY(-50%)",
                    zIndex: 1,
                    display: "flex",
                    flexDirection: "column", // Stack buttons vertically
                    justifyContent: "center",
                }}>
                    {/* Left Center Button */}
                    <button className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "left")}></button>
                    <button className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "left")}></button>
                </div>

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
                    <button className="grid-remove-btn"onClick={() => mediateGridSizeChange('x', -1, "right")}></button>
                    <button className="grid-add-btn"  onClick={() => mediateGridSizeChange('x', 1, "right")}></button>
                </div>

                <div style={{ position: "absolute", bottom: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: 1 }}>
                    {/* Bottom Center Button */}
                    <button className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "bottom")}></button>
                    <button className="grid-remove-btn"  onClick={() => mediateGridSizeChange('y', -1, "bottom")}></button>
                </div>
                
                
            </div>
           
        </div>
    );
};

function DeleteButton({ onDelete }) {
    return (
      <button 
        onClick={onDelete} 
        style={{
            margin: "0px",
            background: 'none',
            border: 'none',
            cursor: 'pointer',
        }}

        
      >
        <TiDelete style={{ padding: "0px", marginTop: "0px",fontSize: "20px"}}/>
        
      </button>
    );
  }
const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex }) => {
   
    const { gardens, handleAddGarden, handleDeleteGarden, handleRenameGarden } = useGardens();

    const btnstyle = {
        width: '120px',
        fontSize: "14px",
        borderColor: 'black'
    };    

    return (
        <div className="garden-bar">
            <div className='garden-bar-item' key={-1}>
                <button 
                    onClick={() => {
                        handleAddGarden();
                        setSelectedGardenIndex(gardens.length);
                    }} 
                    style={{borderRadius: "30px", height: "40px"}}
                >
                    <FaPlus style={{fontSize: "20px" }} />
                </button>
            </div>
               
            {gardens.map((garden, index) => (
                <div className='garden-bar-item' key={index}>
                     <DeleteButton 
                        onDelete={() => {
                            if (gardens.length <= 1) {
                                alert("You cannot delete the last garden.");
                                return;
                            }
                            handleDeleteGarden(index);
                            if (selectedGardenIndex === index) {
                                setSelectedGardenIndex(0);
                            } else if (selectedGardenIndex > index) {
                                setSelectedGardenIndex(selectedGardenIndex - 1);
                            }
                        }} 
                    />
                    
                    
                    <button 
                    onContextMenu={(e) => {
                        e.preventDefault(); // Prevent the default right-click menu
                            handleRenameGarden(selectedGardenIndex);
                        }}
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