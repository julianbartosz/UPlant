// frontend/src/components/sections/plant-search-section/PlantSearchSection.jsx

import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import plantFamilyIcons from '../../../assets/constants/icons'; 

import './styles/plant-search-section.css';



const PlantSearchSection = ({ draggable = true, onPlantClick = () => {} }) => {

    const [searchTerm, setSearchTerm] = useState('');
    const [filteredPlants, setFilteredPlants] = useState([]);

   
    

    const fetchPlants = async (searchTerm) => {
      const url = `http://127.0.0.1:8000/api/v1/plants`; // Updated to include search term in query
      
      try {
          const response = await fetch(url, {
              method: 'GET',
              headers: {
                  'Content-Type': 'application/json',
                  'credentials': 'include',
                  'Accept': 'application/json'
              }

          });
          console.log("Response:", response);
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
        <div className='search-section-container' >
            <div className='search-section-header'>
                <input
                    className='search-input'
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Enter plant name..."
                />
                <button 
                    className='search-button'
                    onClick={() => onSearch(searchTerm)} 
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
      <div className="scrollable-section">
        {Array.isArray(plants) && plants.length > 0 ? (
          plants.map((plant) => (
            <div
              className="plant-item-container"
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
        onClick={() => onPlantClick(plant)} 
      >
        {plant ? (plantFamilyIcons[plant.family] || plantFamilyIcons['default']) : ''}
        <div className="plant-common-name">{plant['common_name']}</div>
      </div>
    );
  };
  
export default PlantSearchSection;