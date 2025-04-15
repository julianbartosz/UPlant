
import React, { useRef, useEffect, useState } from 'react';
import { useDrop } from 'react-dnd';
import plantFamilyIcons from '../../../assets/constants/icons.js'
import { useGardens } from '../../../contexts/ProtectedRoute.jsx';
import { Tooltip } from 'react-tooltip';
import GardenBar from './GardenBar.jsx';
import { CircleButton  } from '../../buttons/index.js';
import useNotifications from '../../../hooks/useNotifications.jsx';
import NotificationsSection from '../notifications-section/NotificationsSection.jsx';

import './styles/garden-section.css';


const GardenSection = () => {

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
                const newSquareSize = Math.min(width * 0.5, height * 0.5) / maxDimension;
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

    const { notifications } = useNotifications();
    const [toggleForm, setToggleForm] = React.useState(false);

    if (!notifications) {
        return <div>Loading...</div>;
    }
  
    return (
        <div className="garden-container" ref={containerRef}>
            <div className="garden-bar-container"> 
                <GardenBar selectedGardenIndex={selectedGardenIndex} setSelectedGardenIndex={setSelectedGardenIndex} />
            </div>


        



            <div className="garden-grid-container">

            <div 
                className="grid-container" 
                ref={drop} 
                style={{
                    width: `${squareSize * gardens[selectedGardenIndex].x}px`, 
                    height: `${squareSize * gardens[selectedGardenIndex].y}px`,
                    marginRight: '40px'
                }}
            >
                <div 
                className="grid" 
                ref={drop} 
                style={{
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
                    <CircleButton className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "top")} />
                    <CircleButton className="grid-remove-btn" onClick={() => mediateGridSizeChange('y', -1, "top")} />
                </div>
                <div style={{
                    position: "absolute",
                    top: "50%", left: "-20px", 
                    transform: "translateY(-50%)",
                    zIndex: 1,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                }}>
                    {/* Left Center Button */}
                    <CircleButton className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "left")} />
                    <CircleButton className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "left")} />
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
                    <CircleButton className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "right")} />
                    <CircleButton className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "right")} />
                </div>

                <div style={{ position: "absolute", bottom: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: 1 }}>
                    {/* Bottom Center Button */}
                    <CircleButton className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "bottom")} />
                    <CircleButton className="grid-remove-btn" onClick={() => mediateGridSizeChange('y', -1, "bottom")} />
                </div>
                
                
            </div>
            
            </div>
            <div className="garden-notification-container">
                <NotificationsSection
                    notifications={notifications}
                    selectedGardenIndex={selectedGardenIndex}
                />

         
            
            </div>
           
        </div>
    );
};


export default GardenSection;