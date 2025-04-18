



import { useUser } from '../hooks/useUser.jsx';
import { useNavigate } from 'react-router-dom';

import React, { useRef, useEffect, useState } from 'react';

import {ICONS} from '../constants/'
import { useGardens } from '../hooks/useGardens';
import { Tooltip } from 'react-tooltip';
import useNotifications from '../hooks/useNotifications.jsx';
import { GardenBar } from '../components/layout';
import NavBar from '../components/layout/NavBar.jsx';
import './styles/notifications-page.css';

function NotificationPage() {

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

    const navigate = useNavigate();

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

    const handleNotificationClick = (plants) => {
        const garden = gardens[selectedGardenIndex];
        const redCells = new Set();
    
        garden.cells.forEach((row, i) => {
            row.forEach((cell, j) => {
                if (cell && plants.some(p => p.id === cell.id)) {
                    redCells.add(`${i}-${j}`);
                }
            });
        });
        console.log("Red cells:", redCells);
    
        setSelectedPlantCells(redCells);
    };
    

return (
    <>
    <div style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
    <NavBar title="Notifications" buttonOptions={['back']} username={username} onBack={ () => { navigate('/dashboard');} } />
      
        <div  style={{
          position: 'fixed', top: '60px', width: 'calc(100vw)',
          height: 'calc(100vh - 60px)', background: 'white',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
        }}>
          
        <div className="garden-container-static" ref={containerRef}>
            <div className="garden-bar-container-static"> 
                <GardenBar dynamic={false} style={{ justifyContent: 'center'}} selectedGardenIndex={selectedGardenIndex} setSelectedGardenIndex={setSelectedGardenIndex} />
            </div>

            <div style={{ margin: '10px 0', width: '100%', display: 'flex', marginTop: '120px', marginBottom: '10px', justifyContent: 'center', flexWrap: 'wrap', gap: '10px' }}>
    {notifications[selectedGardenIndex]?.map((notification, index) => (
        <button
            key={index}
            onClick={() => handleNotificationClick(notification.plants)}
            style={{ padding: '6px 12px', cursor: 'pointer', border: '1px solid #ccc', borderRadius: '5px' }}
        >
            {notification.name}
        </button>
    ))}
</div>


            <div className="garden-grid-container-static" style={{height: `${contentSize}px`}}>

            <div 
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
                        className={`${selectedPlantCells.has(`${i}-${j}`) ? 'notify-square' : 'square'}`}
                        style={{
                            fontSize: `${fontSize}px`,
                        }}
>

                            {item ? (ICONS[item.family] || ICONS['default']) : ""}
                        </div>
                    </div>
                ))
            ))}
                    </div>
                <Tooltip id="my-tooltip" style={{ zIndex: 9999 }}/>
                
            </div>
            
            </div>

        </div>
    
        </div>
    </div>
    </>
  )
}





export default NotificationPage;