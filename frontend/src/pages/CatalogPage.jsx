import { useEffect, useState } from 'react';
import { NavBar, PlantSearchSideBar } from '../components/layout';
import { useUser } from '../hooks/useUser';

import './styles/catalog-page.css';

function Catalog() {
    const { username } = useUser();
    const [selectedPlant, setSelectedPlant] = useState(null);
    const [loading, setLoading] = useState(false);

    const handlePlantClick = (plant) => {
        const fetchPlantDetails = async (plant) => {
            setLoading(true);   
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
                console.log("DATA", data);
                setSelectedPlant(data);
                setLoading(false);
            } catch (error) {
                console.error('Error fetching plant details:', error);
            }
        };
        fetchPlantDetails(plant);
    };
    


    return (
        <>
            <NavBar title="Catalog" username={username} onBack={() => { window.location.href = import.meta.env.VITE_HOME_URL }} />
            <PlantSearchSideBar page="catalog" onPlantClick={handlePlantClick} />
            <div className='catalog-content'>
                {selectedPlant ? (
                    <div className="plant-details-container">
                        <div className="plant-details-section" style={{padding: '0px 20px'}}>
                        <h2>{selectedPlant.common_name}</h2>
                        </div>
                        <div className="plant-details-grid">
                            <div className="plant-details-section">
                                <h3>
                                    Taxonomy
                                    <span className="tooltip">
                                        ?
                                        <span className="tooltip-text">Classification of the plant based on its biological characteristics</span>
                                    </span>
                                </h3>
                                <div className="plant-details-entry">
                                <p><span>Scientific Name:</span> {selectedPlant.scientific_name}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Family:</span> {selectedPlant.family}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Family Common Name:</span> {selectedPlant.family_common_name || 'N/A'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Genus:</span> {selectedPlant.genus}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Status:</span> {selectedPlant.status}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Synonyms:</span> {selectedPlant.synonyms?.slice(0, 3).map(syn => syn.scientific_name).join(', ') || 'None'}</p>
                                </div>
                            </div>

                            <div className="plant-details-section">
                                <h3>
                                    Characteristics
                                    <span className="tooltip">
                                        ?
                                        <span className="tooltip-text">Physical and biological traits of the plant</span>
                                    </span>
                                </h3>
                                <div className="plant-details-entry">
                                <p><span>Edible:</span> {selectedPlant.edible ? 'Yes' : 'No'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Vegetable:</span> {selectedPlant.vegetable ? 'Yes' : 'No'}</p>
                                </div>
                                <div className="plant-details-entry">   
                                <p><span>Growth Rate:</span> {selectedPlant.growth_rate || 'N/A'}</p>
                                </div>
                            </div>

                            <div className="plant-details-section">
                                <h3>
                                    Growing Conditions
                                    <span className="tooltip">
                                        ?
                                        <span className="tooltip-text">Environmental requirements for optimal plant growth</span>
                                    </span>
                                </h3>
                                <div className="plant-details-entry">
                                <p><span>Water Interval:</span> {selectedPlant.water_interval ? `${selectedPlant.water_interval} days` : 'N/A'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Sunlight Requirements:</span> {selectedPlant.sunlight_requirements || 'N/A'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Soil Type:</span> {selectedPlant.soil_type || 'N/A'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>pH Range:</span> {selectedPlant.ph_minimum && selectedPlant.ph_maximum ? `${selectedPlant.ph_minimum} - ${selectedPlant.ph_maximum}` : 'N/A'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Temperature Range:</span> {selectedPlant.min_temperature && selectedPlant.max_temperature ? `${selectedPlant.min_temperature}°C - ${selectedPlant.max_temperature}°C` : 'N/A'}</p>
                                </div>
                            </div>

                            <div className="plant-details-section">
                                <h3>
                                    Phenology
                                    <span className="tooltip">
                                        ?
                                        <span className="tooltip-text">Timing of seasonal biological events in the plant's life cycle</span>
                                    </span>
                                </h3>
                                <div className="plant-details-entry">
                                <p><span>Bloom Months:</span> {selectedPlant.bloom_months?.join(', ') || 'N/A'}</p>
                                </div>
                                <div className="plant-details-entry">
                                <p><span>Fruit Months:</span> {selectedPlant.fruit_months?.join(', ') || 'N/A'}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                ) : <h2 style={{fontSize: '40px', color: 'black', padding: '5px 10px', borderRadius: '5px', background: 'rgba(255, 253, 253, 0.6)'}}>Click to smell the flowers</h2>
                }
            </div>
        </>
    );
}

export default Catalog;