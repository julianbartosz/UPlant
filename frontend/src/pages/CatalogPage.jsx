import { useEffect, useState } from 'react';
import  { NavBar, PlantSearchSideBar }  from '../components/layout';
import { useUser } from '../hooks/useUser';
import './styles/catalog-page.css';

function Catalog() {

    const { username } = useUser();

    const [selectedPlant, setSelectedPlant] = useState(null);
    

    const handlePlantClick = (plant) => {
        console.log("FETCHing, ", plant);
        const fetchPlantDetails = async (plant) => {
            console.log("FETCHing, ", plant);
            if (selectedPlant) {
                try {
                    const response = await fetch(`http://localhost:8000/api/plants/plants/${plant.id}/`, {
                        method: 'GET',
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    const data = await response.json();
                    console.log(data);
                    setSelectedPlant(data);
                } catch (error) {
                    console.error('Error fetching plant details:', error);
                }
            }
        };
        fetchPlantDetails(plant);
        
    };

    useEffect(() => {   
    }, [selectedPlant]);


    return (
        <>
            <NavBar title="Catalog" username = {username} onBack={ () => { window.location.href = process.env.VITE_HOME_URL } }/>
            <PlantSearchSideBar page="catalog" onPlantClick={handlePlantClick} />
            <div className='catalog-content'>
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
        </>
    );
}

export default Catalog;