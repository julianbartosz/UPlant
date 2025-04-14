import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import plantFamilyIcons from '../../../assets/constants/icons'; 
import './styles/plant-search-section.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const PlantSearchSection = ({ draggable = true, onPlantClick = () => {} }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredPlants, setFilteredPlants] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Load initial plants when component mounts
    useEffect(() => {
        fetchPlants();
    }, []);

    const fetchPlants = async (searchTerm = '') => {
        setIsLoading(true);
        setError(null);
        
        let url = `${API_BASE_URL}/plants/`;
        
        // Add search parameter if provided
        if (searchTerm && searchTerm.trim().length > 0) {
            url += `?q=${encodeURIComponent(searchTerm.trim())}`;
        }
        
        try {
            console.log(`Fetching plants from: ${url}`);
            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include', // Correct placement - outside headers
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch plants: ${response.status}`);
            }
            
            const data = await response.json();
            console.log("Plants data:", data);
            
            if (!data.data || !Array.isArray(data.data)) {
                console.error("Unexpected response format:", data);
                setFilteredPlants([]);
                setError("Unexpected data format received");
                return;
            }
            
            setFilteredPlants(data.data);
        } catch (error) {
            console.error("Error fetching plants:", error);
            setError(error.message || "Failed to load plants");
            setFilteredPlants([]);
        } finally {
            setIsLoading(false);
        }
    };

    const onSearch = (term) => {
        if (term.trim().length < 3) {
            setError("Search term must be at least 3 characters long");
            return;
        }
        fetchPlants(term);
    };
    
    return (
        <div className='search-section-container'>
            <div className='search-section-header'>
                <input
                    className='search-input'
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Enter plant name..."
                    onKeyDown={(e) => e.key === 'Enter' && onSearch(searchTerm)}
                />
                <button 
                    className='search-button'
                    onClick={() => onSearch(searchTerm)}
                    disabled={isLoading} 
                >
                    {isLoading ? '⌛' : '🔍'}
                </button> 
            </div>
            
            {error && (
                <div className="error-message">
                    {error}
                </div>
            )}
            
            {isLoading ? (
                <div className="loading-indicator">Loading plants...</div>
            ) : (
                <PlantList 
                    plants={filteredPlants} 
                    draggable={draggable} 
                    onPlantClick={onPlantClick}
                />
            )}
        </div>
    );
};

const PlantList = ({ plants, draggable, onPlantClick }) => {
    if (!Array.isArray(plants) || plants.length === 0) {
        return <div className="no-results">No plants found. Try a different search term.</div>;
    }
    
    return (
        <div className="scrollable-section">
            {plants.map((plant) => (
                <div
                    className="plant-item-container"
                    key={plant.id}
                >
                    <PlantItem
                        plant={plant}
                        draggable={draggable} 
                        onPlantClick={onPlantClick} 
                    />
                </div>
            ))}
        </div>
    );
};
  
const PlantItem = ({ plant, draggable, onPlantClick }) => {
    const [{ isDragging }, drag] = useDrag({
        type: 'PLANT',
        item: plant,
        collect: (monitor) => ({
            isDragging: monitor.isDragging(),
        }),
    });
    
    // Handle null/undefined plant gracefully
    if (!plant) return null;
    
    // Get plant icon based on family or use default
    const plantIcon = plant.family ? 
        (plantFamilyIcons[plant.family] || plantFamilyIcons['default']) : 
        plantFamilyIcons['default'];
    
    return (
        <div
            ref={draggable ? drag : null}
            className="plant-item"
            style={{
                opacity: isDragging ? 0.5 : 1,    
                cursor: draggable ? 'move' : 'pointer', 
            }}
            onClick={() => onPlantClick(plant)} 
        >
            <div className="plant-icon">{plantIcon}</div>
            <div className="plant-info">
                <div className="plant-common-name">{plant.common_name || 'Unknown'}</div>
                <div className="plant-scientific-name">{plant.scientific_name}</div>
            </div>
        </div>
    );
};
  
export default PlantSearchSection;