import { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import SearchPlants from '../components/SearchSection/SearchPlants';
import { useUser } from '../contexts/ProtectedRoute.jsx';

function Catalog() {
    const userContext = useUser();
    const user = userContext?.user; // Use optional chaining
    const [selectedPlant, setSelectedPlant] = useState(null); // State to store the selected plant

    if (!user) {
        return <p>Loading user data...</p>;
    }


    const handlePlantClick = (plant) => {
        console.log('Plant clicked:', plant);
        setSelectedPlant(plant); // Update the selected plant state
    };

    return (
        <>
            <DndProvider backend={HTML5Backend}>
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
                    <SearchPlants draggable={false} onPlantClick={handlePlantClick} />
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
            </DndProvider>
        </>
    );
}

export default Catalog;