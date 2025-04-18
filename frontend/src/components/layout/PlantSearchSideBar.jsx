import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import { ICONS } from '../../constants';
import usePlants from '../../hooks/usePlants';
import { GiGardeningShears } from "react-icons/gi"

import './styles/plant-search-side-bar.css';

const PlantSearchSideBar = ({ draggable = true, shears = true, onPlantClick = () => {}}) => {

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