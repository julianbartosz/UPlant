/**
 * @file PlantSearchSideBar.jsx
 * @description A React component that provides a sidebar for searching and displaying plants,
 * with support for dashboard and catalog pages. Includes plant search functionality
 * and conditional rendering based on page type.
 * @version 1.0.0
 */

import { useState } from 'react';
import { PAGES, ICONS, BASE_API } from '../../constants';
import { IoIosCut } from 'react-icons/io';
import './styles/plant-search-side-bar.css';

const DEBUG = import.meta.env.VITE_DEBUG === 'true';

 /** Ceiling for number of plants in search response */
const MAX_RESPONSE_SIZE = 30;

/**
 * PlantSearchSideBar component for searching and displaying plant information
 * @param {Object} props - Component props
 * @param {string} props.page - The current page ('dashboard' or 'catalog')
 * @param {Function} [props.onShearClick] - Callback for shear action (required for dashboard)
 * @param {Function} [props.onPlantClick] - Callback for plant selection (required for catalog)
 * @returns {JSX.Element} The rendered sidebar component
 * @throws {Error} If page is invalid or required callbacks are missing
 */

const PlantSearchSideBar = ({ page, onShearClick = null, onPlantClick = null }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [plantsList, setPlantsList] = useState(null);

  // Validate props
  if (!page || !PAGES.includes(page)) {
    throw new Error('Invalid page. Use "dashboard" or "catalog".');
  }

  if (page === 'dashboard' && !onShearClick) {
    throw new Error('onShearClick function is required for dashboard page');
  }

  if (page === 'catalog' && !onPlantClick) {
    throw new Error('onPlantClick function is required for catalog page');
  }

  /**
   * Handles plant search API call and updates state with results
   * @async
   */
  const handlePlantSearch = async () => {
    if (DEBUG) {
      console.log('Searching for plants with query:', query);
    }

    if (!query.trim()) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${BASE_API}/api/plants/search/?q=${query}&limit=${MAX_RESPONSE_SIZE}`,
        {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json', 
          },
        }
      );

      if (!response.ok) {
        if (DEBUG) {
          console.log('Failed to fetch plants: ', response);
        }
        alert(`Error: ${response.status} - ${response.statusText}`);
        return;
      }

      const results = await response.json();

      if (DEBUG) {
        console.log('Response Data:', results);
      }

      setPlantsList(
        results.results.filter(
          (plant) => plant.common_name && plant.id && plant.family
        )
      );
    } catch (error) {
      console.error('Error searching plants:', error);
      alert('Failed to search plants. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container">
      <div className="search-header">
        <input
          className="search-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter plant name..."
        />
        <button
          className={loading ? 'loading' : 'search-button'}
          onClick={handlePlantSearch}
          disabled={loading}
        >
          {loading ? '⏳' : '🔍'}
        </button>
      </div>
      <div className="scrollable-section">
        {page === 'dashboard' && (
          <div className="item-container" key={-1}>
            <ShearItem onClick={onShearClick} />
          </div>
        )}
        {Array.isArray(plantsList) && plantsList.length > 0 ? (
          plantsList.map((plant) => (
            <div className="item-container" key={plant.id}>
              <PlantItem plant={plant} onClick={onPlantClick} />
            </div>
          ))
        ) : (
          null
        )}
      </div>
    </div>
  );
};

/**
 * PlantItem component for displaying individual plant information
 * @param {Object} props - Component props
 * @param {Object} props.plant - Plant data object
 * @param {Function} props.onClick - Callback for plant selection
 * @returns {JSX.Element} The rendered plant item
 */
const PlantItem = ({ plant, onClick }) => (
  <div
    className="plant-item"
    onClick={() => onClick(plant)}
  >
    {plant ? ICONS[plant.family] || ICONS.default : null}
    <div className="plant-common-name">{plant?.common_name}</div>
  </div>
);

/**
 * ShearItem component for displaying the shear/remove action
 * @param {Object} props - Component props
 * @param {Function} props.onClick - Callback for shear action
 * @returns {JSX.Element} The rendered shear item
 */
const ShearItem = ({ onClick }) => (
  <div
    className="remove-plant-item"
    onClick={onClick}
  >
    <span role="img" aria-label="shear">
      <IoIosCut />
    </span>
  </div>
);

export default PlantSearchSideBar;