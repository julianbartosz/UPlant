import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import './SearchPlants.css';
import plantFamilyIcons from '../../constants/icons'; 

const SearchPlants = ({ draggable = true, onPlantClick = () => {} }) => {

    const [searchTerm, setSearchTerm] = useState('');
    const [filteredPlants, setFilteredPlants] = useState([]);

    const fetchPlants = async (searchTerm) => {

      const url = `http://127.0.0.1:8000/api/v1/plants`; // TODO: Search not implemented yet

      try {
          const response = await fetch(url, {
              method: 'GET',
              headers: {
                  'Content-Type': 'application/json',
                  'credentials': 'include'
              }
          });
          if (!response.ok) {
              throw new Error("Failed to fetch plants");
          }
          const plants = await response.json();
          setFilteredPlants(plants['data']);
      }

      catch (error) {
          console.error("Error fetching plants:", error);
          setFilteredPlants([]); 
          return;
      }
  };

    const onSearch = (term) => {
      // TODO: Add debounce or throttle here if needed
      // TODO: Add validation
      if (term.trim().length < 3) {
        console.warn("Search term must be at least 3 characters long.");
        return;
      }
      fetchPlants(term);
    };
    
    return (
        <div>
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', marginBottom: '10px' }}>
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Enter plant name..."
                    style={{ width: '150px', border: 'none', outline: 'none', fontSize: '16px' }}
                />
                <button 
                    onClick={() => onSearch(searchTerm)} 
                    style={{ 
                        background: 'none', 
                        border: 'none', 
                        cursor: 'pointer', 
                        fontSize: '20px' 
                    }}
                    onMouseDown={(e) => e.target.style.transform = 'scale(0.9)'} // Shrink on click
                    onMouseUp={(e) => e.target.style.transform = 'scale(1)'} // Reset after click
                    onMouseLeave={(e) => e.target.style.transform = 'scale(1)'} // Reset if mouse leaves
                >
                    🔍
                </button> 
            </div>
            <PlantList 
            plants={filteredPlants} 
            draggable={draggable} 
            onPlantClick={onPlantClick}
            />
        </div>
    );
};


const PlantList = ({ plants, draggable, onPlantClick }) => {
    return (
      <div
        className="scrollable-section"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          width: '100%',
          height: 'calc(100vh - 150px)',
        }}
      >
        {Array.isArray(plants) && plants.length > 0 ? (
          plants.map((plant) => (
    
            <div
              key={plant.id}
              style={{
                fontSize: '21px',
                flex: '1 0 50%',
                boxSizing: 'border-box',
                padding: '10px',
              }}
            >
              <PlantItem
                plant={plant}
                draggable={draggable} 
                onPlantClick={ onPlantClick } 
              />
            </div>
          ))
        ) : (
          <div style={{ fontSize: '18px', padding: '10px' }}>No plants found</div>
        )}
      </div>
    );
  };
  
  const PlantItem = ({ plant, draggable, onPlantClick }) => {
    // If draggable is true, use drag-and-drop, else, use the click handler
    const [{ isDragging }, drag] = useDrag({
      type: 'PLANT',
      item: plant,
      collect: (monitor) => ({
        isDragging: monitor.isDragging(),
      }),
    });
    
    return (
      <div
        ref={draggable ? drag : null} // Apply the drag ref only if draggable
        className="plant-item"
        style={{
          textAlign: 'center',
          opacity: isDragging ? 0.5 : 1,    // Optional: Semi-transparent when dragging
          transition: 'background-color 0.2s ease, opacity 0.2s ease', // Smooth transition
          cursor: draggable ? 'move' : 'pointer', // Change cursor style based on draggable state
        }}
        onClick={() => onPlantClick(plant)} 
      >
        {plant ? (plantFamilyIcons[plant.family] || plantFamilyIcons['default']) : ''}
        <div style={{ fontSize: '14px', marginTop: '5px' }}>{plant['common_name']}</div>
      </div>
    );
  };
  
  
export default SearchPlants;