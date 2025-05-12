/**
 * @file PlantSearchSideBar.jsx
 * @version 1.0.0
 * @description A React component that provides a sidebar for searching and displaying plants,
 * with support for dashboard and catalog pages. Includes plant search functionality
 * and conditional rendering based on page type.
 * 
 * @component
 * @param {Object} props - The component props.
 * @param {string} props.page - The current page type ('dashboard' or 'catalog').
 * @param {Function} [props.onShearClick] - Callback function for shear action (required for 'dashboard' page).
 * @param {Function} [props.onPlantClick] - Callback function for plant selection (required for 'catalog' page).
 * @returns {JSX.Element} The rendered PlantSearchSideBar component.
 * 
 * @details
 * - The component allows users to search for plants by name and displays the results in a scrollable section.
 * - The sidebar includes a shear item for the dashboard page and plant items for both dashboard and catalog pages.
 * - The component handles API requests to fetch plant data and manages loading states.
 * - It validates the required props based on the current page type and provides error handling for API requests.
 */

import { useEffect, useState } from 'react';
import { PAGES, ICONS, BASE_API } from '../../constants';
import { IoIosCut } from 'react-icons/io';
import { DEBUG, MAX_RESPONSE_PLANTS } from '../../constants';
import { ThreeDots } from 'react-loader-spinner';
import './styles/plant-search-side-bar.css';

// Term for initalizing plantlist
// Yields diverse icons
const QUERY_ON_MOUNT = "q";

/**
 * Fetches plants based on the search query
 * @param {string} query
 * @returns {Promise<Array>}
 */
const fetchPlants = async (query) => {
  if (DEBUG) {
    console.log('Searching for plants with query:', query);
  }

  if (!query.trim()) {
    return [];
  }

  try {
    const response = await fetch(
      `${BASE_API}/plants/search/?q=${query}&limit=${MAX_RESPONSE_PLANTS}`,
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
      return [];
    }

    const results = await response.json();

    if (DEBUG) {
      console.log('Response Data:', results);
    }

    return results.results.filter(
      (plant) => plant.common_name && plant.id && plant.family
    );
  } catch (error) {
    console.error('Error searching plants:', error);
    alert('Failed to search plants. Please try again.');
    return [];
  }
};

const PlantSearchSideBar = ({ page, onShearClick = null, onPlantClick = null }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    if (DEBUG) {
      console.log('Component mounted. Fetching initial plants...');
    }

    // Fetch initial plants on mount
    const fetchInitialPlants = async () => {
      // Loading on mount
      const initialPlants = await fetchPlants(QUERY_ON_MOUNT);
      setPlantsList(initialPlants);
      setLoading(false);
    };

    fetchInitialPlants();
  }, []);

  /**
   * Handles plant search and updates state with results
   * @async
   */
  const handlePlantSearch = async () => {
    setLoading(true);
    const plants = await fetchPlants(query);
    setPlantsList(plants);
    setLoading(false);
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
          className={loading ? 'search-loading' : 'search-button'}
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
        {Array.isArray(plantsList) && !loading ? (
          plantsList.length > 0 ? (
            plantsList.map((plant) => (
              <div className="item-container" key={plant.id}>
                <PlantItem plant={plant} onClick={onPlantClick} />
              </div>
            ))
          ) : (
            <div style={{ marginTop: '20px', textAlign: 'center', color: 'rgb(177, 174, 174)' }}>
              🌱 We couldn't find any plants matching your search . Maybe try a different term? 🌿
            </div>
          )
        ) : (
          <div style={{ marginTop: '25px', width: '100%', height: 'calc(100% - 88px)',display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <ThreeDots 
              height="80"
              width="80"
              radius="9"
              color="rgb(177, 174, 174)"
              ariaLabel="three-dots-loading"
              wrapperStyle={{}}
              wrapperClassName=""
              visible={true}
            />
          </div>
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