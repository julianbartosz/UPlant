import  { NavBar, PlantSearchSideBar }  from '../components/layout';
import { useUser } from '../hooks/useUser';
import './styles/catalog-page.css';

function Catalog() {

    const { username, selectedPlant, setSelectedPlant } = useUser();
    
    if (!username) {
        return <p>Loading user data...</p>;
    }

    const handlePlantClick = (plant) => {
        console.log(plant);
    };

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