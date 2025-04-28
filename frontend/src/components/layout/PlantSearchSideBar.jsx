import { useState } from 'react';
import { PAGES, ICONS } from '../../constants';
import { usePlants } from '../../hooks';
import { IoIosCut } from "react-icons/io";
import './styles/plant-search-side-bar.css';

const PlantSearchSideBar = ({ page, onShearClick = null, onPlantClick = null }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const { 
      plantsList, 
      loading: plantsListLoading, 
      mediatePlantSearch 
    } = usePlants();
    
    if (!page || !PAGES.includes(page)) {
      throw new Error('Invalid page. Use "dashboard" or "catalog".');
    }

    if (page === 'dashboard' && !onShearClick) {
      throw new Error('onShearClick function is required for dashboard page');
    }

    if (page === 'catalog' && !onPlantClick) {
      throw new Error('setSelectedPlant function is required for catalog page');
    }

    return (
      <div className="search-container">
        <div className="search-header">
          <input
            className="search-input"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Enter plant name..."
          />
          
            {plantsListLoading ? (
              <button className="loading">⏳</button>
            ) : (
              <button
            className="search-button"
            onClick={() => mediatePlantSearch(searchTerm)}
          >
              🔍
              </button>
            )}
  
        </div>
        <div className="scrollable-section">
          {page == 'dashboard' && (
            <div className="item-container" key={-1}>
              <ShearItem onClick={onShearClick} />
            </div>
          )}
          {Array.isArray(plantsList) && plantsList.length > 0 ? (
            plantsList.map((plant) => (
              <div className="item-container" key={plant.id}>
                <PlantItem
                  plant={plant}
                  onClick={() => {onPlantClick(plant);}}
                />
              </div>
            ))
          ) : (
            ''
          )}
        </div>
      </div>
      );
    };

const PlantItem = ({ plant, onClick }) => {

    return (
      <div
        className="plant-item"
        style={{
          cursor: 'pointer',
        }}
        onClick={() => onClick(plant)}
      >
        {plant ? (ICONS[plant.family] || ICONS['default']) : ''}
        <div className="plant-common-name">{plant['common_name']}</div>
      </div>
    );
  };

const ShearItem = ({ onClick }) => {

    return (
      <div
      className="remove-plant-item"
      style={{
        cursor: 'pointer'
      }}
      onClick={onClick}
      >
      <span
        role="img"
        aria-label="fire"
      >
        <IoIosCut />
      </span>
      </div>
    );
  };

export default PlantSearchSideBar;
