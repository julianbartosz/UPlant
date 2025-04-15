import { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import  { NavBarSection, PlantSearchSection }  from '../components/sections';
import { useUser } from '../hooks/useUser';
import { getPlantById } from '../services/trefleService.js';

function Catalog() {

    const { username, selectedPlant, setSelectedPlant } = useUser();
    
    if (!username) {
        return <p>Loading user data...</p>;
    }

    const handlePlantClick = (plant) => {
        console.log('Plant clicked:', plant);
        getPlantById(plant.id).then((plantData) => {
            console.log('Plant data:', plantData);
            setSelectedPlant(plantData);
        });
    };

    return (
        <>
            <DndProvider backend={HTML5Backend}>
            <div className='app' style={{ backgroundColor: 'white', width: '100vw', height: '100vh', position: 'relative' }}>
            <NavBarSection title="Catalog" username = {username} onBack={ () => { window.location.href = 'http://localhost:8000/' } }/>
                
                <div
                    className="sidebar"
                    style={{
                        position: 'fixed',
                        top: '60px',
                        left: 0,
                        width: '200px',
                        height: 'calc(100vh - 60px)',
                        background: 'linear-gradient(to right, rgb(152, 152, 152),rgb(65, 64, 64))',
                        padding: '10px',
                        zIndex: 5,
                        borderRadius: '0 10px 0 0',
                        color: 'black', // Set text color to black
                    }}
                >
                    <PlantSearchSection draggable={false} onPlantClick={handlePlantClick} />
                </div>
                <div
                    style={{
                        position: 'fixed',
                        top: '60px',
                        left: '240px',
                        width: 'calc(100vw - 240px)',
                        height: 'calc(100vh - 60px)',
                        background: 'white',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        padding: '20px',
                        color: 'black', // Set text color to black
                    }}
                >
                    
                    {selectedPlant ? (
                        <div>
                            <h2>{selectedPlant.common_name}</h2>
                            <p>Family: {selectedPlant.family}</p>
                            <p>Family Common Name: {selectedPlant.family_common_name || 'N/A'}</p>
                            <p>Scientific Name: {selectedPlant.scientific_name}</p>
                            {selectedPlant.image_url && (
                                <img
                                    src={selectedPlant.image_url}
                                    alt={selectedPlant.common_name}
                                    style={{ maxWidth: '100%', maxHeight: '200px', marginTop: '10px' }}
                                />
                            )}
                        </div>
                    ) : (
                        <p>Select a plant to see its details</p>
                    )}
                </div>
                </div>
            </DndProvider>
        </>
    );
}

export default Catalog;