import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import { ICONS } from '../../constants';
import usePlants from '../../hooks/usePlants';
import { GiGardeningShears } from "react-icons/gi"

import './styles/plant-search-side-bar.css';

const PlantSearchSideBar = ({ draggable = true, shears = true, onPlantClick = () => {}}) => {

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
            <ScrollableSection
            plants={plantsList} 
            draggable={draggable} 
            shears={shears}
            onPlantClick={onPlantClick}
            />
        </div>
    );
};


const ScrollableSection = ({ plants, draggable, shears, onPlantClick,  }) => {

    return (
      <div className="scrollable-section">
        {shears && (
        <div className="item-container" key={-1}>
            <ShearItem
              draggable={draggable}
              onPlantClick={onPlantClick}
            />
        </div>
      )}
        {Array.isArray(plants) && plants.length > 0 ? (
          plants.map((plant) => (
            <div
              className="item-container"
              key={plant.id}
            >
              <PlantItem
                plant={plant}
                draggable={draggable} 
                onPlantClick={ onPlantClick } 
              />
            </div>
          ))
        ) : (
          ""
        )}
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
    
    return (
      <div
        ref={draggable ? drag : null}
        className="plant-item"
        style={{
          opacity: isDragging ? 0.5 : 1,    
          cursor: draggable ? 'move' : 'pointer', 
        }}
        onClick={() => {}} 
      >
        {plant ? (ICONS[plant.family] || ICONS['default']) : ''}
        <div className="plant-common-name">{plant['common_name']}</div>
      </div>
    );
  };

  const ShearItem = ({ draggable, onPlantClick }) => {
    const [{ isDragging }, drag] = useDrag({
      type: 'SHEAR',
      item: { type: 'SHEAR'},
      collect: (monitor) => ({
        isDragging: monitor.isDragging(),
      }),
    });
    
    return (
      <div
        ref={draggable ? drag : null}
        className="remove-plant-item"
        style={{
          opacity: isDragging ? 0.5 : 1,    
          cursor: draggable ? 'move' : 'pointer', 
        }}
        onClick={() => {}} 
      >
        <GiGardeningShears color='black'/>
      </div>
    );
  };
  
export default PlantSearchSideBar;