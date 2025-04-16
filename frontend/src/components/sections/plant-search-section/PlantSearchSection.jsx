import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import plantFamilyIcons from '../../../assets/constants/icons'; 
import usePlants from '../../../hooks/usePlants';

import './styles/plant-search-section.css';

const PlantSearchSection = ({ draggable = true, onPlantClick = () => {} }) => {

    const [searchTerm, setSearchTerm] = useState('');
    const {plantsList, mediatePlantSearch } = usePlants();

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
                    onClick={() => mediatePlantSearch(searchTerm)} 
                >
                    🔍
                </button> 
            </div>
            <PlantList 
            plants={plantsList} 
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
        onClick={() => {}} 
      >
        {plant ? (plantFamilyIcons[plant.family] || plantFamilyIcons['default']) : ''}
        <div className="plant-common-name">{plant['common_name']}</div>
      </div>
    );
  };
  
export default PlantSearchSection;