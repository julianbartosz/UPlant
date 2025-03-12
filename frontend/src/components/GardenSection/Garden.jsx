// frontend/src/components/GardenSection/Garden.jsx

import React, { useRef, useEffect, useState } from 'react';
import './Garden.css';
import { useDrop } from 'react-dnd';
import { FaPlus } from 'react-icons/fa';

// GET
const fetchGardens = (/* some unique userIdentifier */) => {

    // NOTE: Placeholder; will be part of garden data
    const cells = [
        ["🍅", "🥕", "🌽", "🍆", "🥦"],
        ["🌳", "🌲", null, null, null],
        Array(5).fill(null),
        Array(5).fill(null),
        Array(5).fill(null),
    ];

    // TODO: Retrieve Gardens
    let gardens = [
        { name: 'Garden 1', x: 5, y: 5, cells: cells },
        { name: 'Garden 2', x: 5, y: 5, cells: cells },
        { name: 'Garden 3', x: 5, y: 5, cells: cells }
    ];
  
    //  NOTE: Example of fetching data from the backend
    // try {
    //     const response = await fetch('/api/gardens');
    //     const data = await response.json();
    //     setGardens(data);
    // } catch (error) {
    //     console.error('Error fetching gardens:', error);
    // }

    return gardens;
};

// POST
const updateGarden = async (/* unique gardena nd user identifier */) => {
    // TODO: Implement updateGarden

    //  NOTE: Example of posting data to the backend
    // try {
    //     const response = await fetch(`/api/gardens/${gardenId}`, {
    //         method: 'PUT',
    //         headers: {
    //             'Content-Type': 'application/json',
    //         },
    //         body: JSON.stringify(updatedGarden),
    //     });
    //     const data = await response.json();
    //     setGardens((prevGardens) =>
    //         prevGardens.map((garden) =>
    //             garden.id === gardenId ? data : garden
    //         )
    //     );
    // } catch (error) {
    //     console.error('Error updating garden:', error);
    // }

    return None

};

// DELETE
const deleteGarden = async (/* unique gardena nd user identifier */) => {
    // TODO: Implement deleteGarden

    //  NOTE: Example of deleting data from the backend
    // try {
    //     const response = await fetch(`/api/gardens/${gardenId}`, {
    //         method: 'DELETE',
    //     });
    //     if (response.ok) {
    //         setGardens((prevGardens) =>
    //             prevGardens.filter((garden) => garden.id !== gardenId)
    //         );
    //     }
    // } catch (error) {
    //     console.error('Error deleting garden:', error);
    // }    

    return None

};


const Garden = ({ username }) => {
    // Type or types of useDrop objects accepted for drops
    const accept = 'PLANT';

    const containerRef = useRef(null);
    const [fontSize, setFontSize] = useState(40); // Default font size
    const [selectedGardenIndex, setSelectedGardenIndex] = useState(0); // Track selected garden
    const [gardens, setGardens] = useState(fetchGardens());

    useEffect(() => {
        const loadGardens = async () => {
            const fetchedGardens = fetchGardens();
            setGardens(fetchedGardens);
        };
        loadGardens();
    }, []);

    const DropTarget = (value, i, j) => {

        const [, drop] = useDrop(() => ({
            accept,
            drop: (item) => {
            console.log('Dropped item:', item.name, 'into cell:', i, j);
    
            gardens[selectedGardenIndex].cells[i][j] = item.name;
            setGardens([...gardens]);
            },
        }));
      
        return <div key={`${i}-${j}`} ref={drop} className="square" style={{ fontSize: `${fontSize}px` }}>
        {value || ""}
    </div>
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
    
    useEffect(() => {
        
        const updateFontSize = () => {
            if (containerRef.current) {
                const containerWidth = containerRef.current.offsetWidth;
                const containerHeight = containerRef.current.offsetHeight;
                
                // Dynamically calculate font size
                const calculatedFontSize = Math.min(containerWidth / gardens[selectedGardenIndex].x, containerHeight / gardens[selectedGardenIndex].y) * 0.5;
                setFontSize(calculatedFontSize);
            }
        };

        // Call initially and add a resize event listener
        updateFontSize();
        window.addEventListener('resize', updateFontSize);

        return () => window.removeEventListener('resize', updateFontSize);
    }, [gardens[selectedGardenIndex].x, gardens[selectedGardenIndex].y]); // Recalculate when dimensions change


    const createGrid = () => {
        return gardens[selectedGardenIndex].cells.map((row, i) => (
            <div key={i} className="row">
                {row.map((value, j) => (
                    DropTarget(value, i, j)
                ))}
            </div>
        ));
    };

    return (
        <div className="container" ref={containerRef}>
            <div style={{ position: "absolute", top: 0, left: 0}}>
            <GardenBar gardens={gardens} selectedGardenIndex={selectedGardenIndex} setSelectedGardenIndex={setSelectedGardenIndex}/>
            </div>

            <div className="garden" style={{ 
                display: "grid",
                gridTemplateRows: `repeat(${gardens[selectedGardenIndex].y}, 1fr)`,
                gridTemplateColumns: `repeat(${gardens[selectedGardenIndex].x}, 1fr)`,
            }}>
                {createGrid()}
            </div>
        </div>
    );
};

const GardenBar = ({ gardens, selectedGardenIndex, setSelectedGardenIndex }) => {

    const btnstyle = {
        width: '120px',
        fontSize: "14px",
        borderColor: 'black'
    };    

    return (
        <div className="garden-bar">
            <div className='garden-bar-item' key={-1}>
                <button style={{borderRadius: "30px", height: "40px"}}>
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