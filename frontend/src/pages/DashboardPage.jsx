



import { useUser } from '../hooks/useUser.jsx';

import React, { useRef, useEffect, useState } from 'react';
import { useDrop } from 'react-dnd';
import {ICONS} from '../constants/'
import { useGardens } from '../hooks/useGardens';
import { Tooltip } from 'react-tooltip';
import { CircleButton  } from '../components/buttons'
import useNotifications from '../hooks/useNotifications.jsx';
import { NotificationSection, GardenBar, PlantSearchSideBar } from '../components/layout';
import NavBar from '../components/layout/NavBar.jsx';
import './styles/dashboard-page.css';

import { 
    FaArrowDown, 
    FaArrowLeft, 
    FaArrowRight, 
    FaArrowUp 
} from 'react-icons/fa';

const MAXSIZE_GARDEN = 10;

function DashboardPage() {

    const { 
        username,
        usernameError
    } = useUser();

    const { 
        notifications,
        notificationsLoading,
        notificationsError,
    } = useNotifications();

    const { 
        gardens, 
        setGardens,
        mediateUpdateGarden,
        mediateRenameGarden,
        mediateAddGarden,
        mediateDeleteGarden,
        gardensLoading,
        gardensError
        
    } = useGardens(); 


    if (notificationsLoading) {
        return <p>Loading notifications...</p>;
    }

    if (gardensLoading) {
        return <p>Loading gardens...</p>;
    }

    if (!gardens) {
        return <p>No gardens available.</p>;
    }

    if (gardensError || notificationsError || usernameError) {
        console.error('Error fetching data:', gardensError, notificationsError, usernameError);
        return <p>Error fetching data.</p>;
    } 

    const accept = ['PLANT', 'SHEAR']

    const [squareSize, setSquareSize] = useState(1);
    const [fontSize, setFontSize] = useState(null); 
    const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
    const [dugCells, setDugCells] = useState(new Set());
    const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());

    const [contentSize, setContentSize] = useState(500);
    const containerRef = useRef(null);
    const dugCellsRef = useRef(dugCells);
    const selectedPlantCellsRef = useRef(selectedPlantCells);
    const selectedGardenIndexRef = useRef(selectedGardenIndex); 

    useEffect(() => {
        dugCellsRef.current = dugCells;
    }, [dugCells]);

    useEffect(() => {
        selectedPlantCellsRef.current = selectedPlantCells;
    }, [selectedPlantCells]);
    

    useEffect(() => {
        selectedGardenIndexRef.current = selectedGardenIndex;
        setDugCells(new Set()); 
        setSelectedPlantCells(new Set());

        const handleResize = () => {
            if (containerRef.current) {
                const { width, height } = containerRef.current.getBoundingClientRect();
                const maxDimension = Math.max(gardens[selectedGardenIndex].x, gardens[selectedGardenIndex].y);
                const newSquareSize = Math.min(width * 0.6, height * 0.6) / maxDimension;
                console.log("Old square size:", squareSize);
                setFontSize(newSquareSize * 0.5);
                setContentSize(height - 88);
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
    const mediateGridSizeChange = (axis, change, edge) => {
        const newGarden = { ...gardens[selectedGardenIndex] };

        if (axis === 'x') {
            if (newGarden.x + change > MAXSIZE_GARDEN) {
                alert(`Cannot resize: Maximum garden width of ${MAXSIZE_GARDEN} reached.`);
                return;
            }

            if (newGarden.x + change < 1) {
                alert('Cannot resize: Garden width cannot be smaller than 1.');
                return;
            }

            if (change < 0) {
                const columnIndex = edge === 'left' ? 0 : newGarden.x - 1;
                const hasPlant = newGarden.cells.some(row => row[columnIndex] !== null);
                if (hasPlant) {
                    alert('Cannot resize: Plants would be deleted.');
                    return;
                }
            }

            newGarden.x += change;
            if (edge === 'left') {
                newGarden.cells.forEach(row => change > 0 ? row.unshift(null) : row.shift());
            } else if (edge === 'right') {
                newGarden.cells.forEach(row => change > 0 ? row.push(null) : row.pop());
            }

        } else if (axis === 'y') {
            if (newGarden.y + change > MAXSIZE_GARDEN) {
                alert(`Cannot resize: Maximum garden height of ${MAXSIZE_GARDEN} reached.`);
                return;
            }

            if (newGarden.y + change < 1) {
                alert('Cannot resize: Garden height cannot be smaller than 1.');
                return;
            }

            if (change < 0) {
                const rowIndex = edge === 'top' ? 0 : newGarden.y - 1;
                const hasPlant = newGarden.cells[rowIndex].some(cell => cell !== null);
                if (hasPlant) {
                    alert('Cannot resize: Plants would be deleted.');
                    return;
                }
            }

            newGarden.y += change;
            if (edge === 'top') {
                change > 0 ? newGarden.cells.unshift(Array(newGarden.x).fill(null)) : newGarden.cells.shift();
            } else if (edge === 'bottom') {
                change > 0 ? newGarden.cells.push(Array(newGarden.x).fill(null)) : newGarden.cells.pop();
            }
        }

        mediateUpdateGarden(newGarden, false);
    };    const isSelected = (i, j) => dugCells.has(`${i}-${j}`);
        const isSelectedShear = (i, j) => selectedPlantCells.has(`${i}-${j}`);
        

        const cellClickHandler = (obj, i, j) => { 
            const isTaken = obj !== null;

            if (!isTaken) {
                const newSet = new Set(dugCells); 
                const key = `${i}-${j}`;
        
                if (newSet.has(key)) {
                    newSet.delete(key); 
                } else {
                    newSet.add(key); 
                }
                setDugCells(newSet);
            } else {

                const newSet = new Set(selectedPlantCells); 
                const key = `${i}-${j}`;
        
                if (newSet.has(key)) {
                    newSet.delete(key); 
                } else {
                    newSet.add(key); 
                }
                setSelectedPlantCells(newSet);   
        }
    }

  
    const [, drop] = useDrop(() => ({
        accept,
        drop: (item) => {
                if (item.type === 'SHEAR') {
                    console.log("SSSSSSSSS:", item);
                    setGardens((prevGardens) => {

                        console.log("START", selectedPlantCellsRef.current);
        
                        const currentGarden = { ...prevGardens[selectedGardenIndexRef.current] };
                        if (!currentGarden) {
                            console.error("Garden not found at index:", selectedGardenIndexRef.current);
                            return prevGardens;
                        }
        
                        const newCells = [...currentGarden.cells];
        
                        selectedPlantCellsRef.current.forEach(key => {
                            const [row, col] = key.split('-').map(Number);
                            if (row < currentGarden.y && col < currentGarden.x) {
                                console.log("XXXXXXXX", row, col);
                                newCells[row][col] = null;
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
                    return;

                }    
                
                setGardens((prevGardens) => {
                        console.log("PPPPPP")
                        console.log("START", dugCellsRef.current);
            
                    const currentGarden = { ...prevGardens[selectedGardenIndexRef.current] };
                    if (!currentGarden) {
                        console.error("Garden not found at index:", selectedGardenIndexRef.current);
                        return prevGardens;
                    }

                    const newCells = [...currentGarden.cells];

                    dugCellsRef.current.forEach(key => {
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

    
    const [toggleForm, setToggleForm] = React.useState(false);

    
    console.log("GardenDashboard user:", username);

return (
    <>
    <div style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
    <NavBar title="Dashboard" username={username} onBack={ () => { window.location.href = 'http://localhost:8000/' } } />
      

        <div className="sidebar" style={{
          position: 'fixed', top: '60px', left: 0, width: '200px', height: 'calc(100vh - 60px)',
          background: 'linear-gradient(to right, rgb(152, 152, 152),rgb(65, 64, 64))', padding: '10px', zIndex: 5
          , borderRadius: '0 10px 0 0'
        }}>
          <PlantSearchSideBar />
        </div>
        <div  style={{
          position: 'fixed', top: '60px', left: '240px', width: 'calc(100vw - 200px)',
          height: 'calc(100vh - 60px)', background: 'white',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
        }}>
          
        <div className="garden-container" ref={containerRef}>
            <div className="garden-bar-container"> 
                <GardenBar selectedGardenIndex={selectedGardenIndex} setSelectedGardenIndex={setSelectedGardenIndex} />
            </div>

            <div className="garden-grid-container" style={{height: `${contentSize}px`}}>

            <div 
                ref={drop}
                className="grid-container" 
                style={{
                    width: `${squareSize * gardens[selectedGardenIndex].x}px`, 
                    height: `${squareSize * gardens[selectedGardenIndex].y}px`,
                }}
            >
                <div 
                className="grid" 
                style={{
                    gridTemplateColumns: `repeat(${gardens[selectedGardenIndex].x}, ${squareSize}px)`, 
                    gridTemplateRows: `repeat(${gardens[selectedGardenIndex].y}, ${squareSize}px)`,
                }}
            >
                
            {gardens[selectedGardenIndex].cells.map((row, i) => (
                row.map((item, j) => (
                    <div  key={`${i}-${j}`} data-tooltip-id="my-tooltip" data-tooltip-content={item ? item['common_name'] : ""}>
                        <div
                            className={`square ${isSelected(i, j) ? 'selected' : ''} ${isSelectedShear(i, j) ? 'selected-shear' : ''}`}
                            style={{ fontSize: `${fontSize}px` }}
                            onClick={() => {cellClickHandler(item, i, j)}}
                        >
                            {item ? (ICONS[item.family] || ICONS['default']) : ""}
                        </div>
                    </div>
                ))
            ))}
                    </div>
                <Tooltip id="my-tooltip" style={{ zIndex: 9999 }}/>
                <div style={{ position: "absolute", top: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: -0.5,display: "flex" }}>
                    {/* Top Center Button */}
                    <CircleButton  text={<FaArrowUp />}  className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "top")} />
                    <CircleButton  text={<FaArrowDown />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('y', -1, "top")} />
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
                    <CircleButton text={<FaArrowRight />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "left")} />
                    <CircleButton text={<FaArrowLeft />} className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "left")} />
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
                    <CircleButton text={<FaArrowLeft />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "right")} />
                    <CircleButton text={<FaArrowRight />} className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "right")} />
                </div>

                <div style={{ position: "absolute", bottom: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: 1, display: "flex",}}>
                    {/* Bottom Center Button */}
                    <CircleButton text={<FaArrowDown />} className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "bottom")} />
                    <CircleButton text={<FaArrowUp />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('y', -1, "bottom")} />
                </div>
                
                
            </div>
            
            </div>
            <div className="garden-notification-container" style={{borderTop: '2px solid white',  alignSelf: 'end', height: `${contentSize}px`, marginRight: '40px'}}>
                <NotificationSection
                    contentSize={contentSize}
                    notifications={notifications}
                    selectedGardenIndex={selectedGardenIndex}
                    plantOptions={[...new Set(gardens[selectedGardenIndex].cells.flat().filter(item => item !== null))]}
                />
            
            </div>
           
        </div>
    
        </div>
    </div>
    </>
  )
}





export default DashboardPage;