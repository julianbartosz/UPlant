/**
 * @file Catalog.jsx
 * @version 1.0.1
 * @description A catalog page component that displays detailed information about plants.
 * This component allows users to browse and view comprehensive details about various plants,
 * including taxonomy, characteristics, growing conditions, and phenology.
 * 
 * @component
 * @returns {JSX.Element} The rendered Catalog component.
 * 
 */
import { useState } from 'react';
import { NavBar, PlantSearchSideBar } from '../components/layout';
import { GridLoading } from '../components/widgets';
import { DEBUG, HOME_URL, BASE_API } from '../constants';
import './styles/catalog-page.css';

/**
 * Fetches detailed information about a specific plant from the API
 * 
 * @param {Object} plant - Basic plant information containing at least an id
 * @returns {Promise<Object>} - Detailed plant information
 * @throws {Error} - If the network request fails
 */
const fetchPlantDetails = async (plant) => {
    if (DEBUG) {
        console.log('--- Fetching Plant Details ---');
        console.log('Selected Plant:', plant);
    }
  try {
    const response = await fetch(`${BASE_API}/plants/plants/${plant.id}/`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    const data = await response.json();
    if (DEBUG) console.log("Selected plant details:", data);
    return data;
  } catch (error) {
    console.error('Error fetching plant details:', error);
    throw error;
  }
};

/**
 * PlantDetailsSection component for displaying a section of plant details
 * 
 * @param {Object} props - Component props
 * @param {string} props.title - Section title
 * @param {string} props.tooltip - Tooltip text for this section
 * @param {React.ReactNode} props.children - Child components (detail entries)
 * @returns {JSX.Element}
 */
const PlantDetailsSection = ({ title, tooltip, children }) => (
  <div className="plant-details-section">
    <h3>
      {title}
      <span className="tooltip">
        ?
        <span className="tooltip-text">{tooltip}</span>
      </span>
    </h3>
    {children}
  </div>
);

/**
 * PlantDetailEntry component for displaying a single plant detail
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Detail label
 * @param {React.ReactNode} props.value - Detail value
 * @returns {JSX.Element}
 */
const PlantDetailEntry = ({ label, value }) => (
  <div className="plant-details-entry">
    <p><span>{label}:</span> {value}</p>
  </div>
);

/**
 * Catalog component for browsing and viewing detailed plant information
 * 
 * @returns {JSX.Element}
 */
function Catalog() {
  const [selectedPlant, setSelectedPlant] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePlantClick = async (plant) => {
    setLoading(true);
    try {
      const plantData = await fetchPlantDetails(plant);
      setSelectedPlant(plantData);
    } catch (error) {
      // Error already logged in the fetchPlantDetails function
    } finally {
      setLoading(false);
    }
  };

  /**
   * Renders the plant details view when a plant is selected
   * 
   * @param {Object} plant - The selected plant data
   * @returns {JSX.Element}
   */
  const renderPlantDetails = (plant) => (
    <div className="plant-details-container">
      <div className="plant-details-section" style={{ padding: '0px 20px' }}>
        <h2>{plant.common_name}</h2>
      </div>
      
      <div className="plant-details-grid">
        {/* Taxonomy Section */}
        <PlantDetailsSection 
          title="Taxonomy" 
          tooltip="Classification of the plant based on its biological characteristics"
        >
          <PlantDetailEntry label="Scientific Name" value={plant.scientific_name} />
          <PlantDetailEntry label="Family" value={plant.family} />
          <PlantDetailEntry label="Family Common Name" value={plant.family_common_name || 'N/A'} />
          <PlantDetailEntry label="Genus" value={plant.genus} />
          <PlantDetailEntry label="Status" value={plant.status} />
          <PlantDetailEntry 
            label="Synonyms" 
            value={plant.synonyms?.slice(0, 3).map(syn => syn.scientific_name).join(', ') || 'None'} 
          />
        </PlantDetailsSection>

        {/* Characteristics Section */}
        <PlantDetailsSection 
          title="Characteristics" 
          tooltip="Physical and biological traits of the plant"
        >
          <PlantDetailEntry label="Edible" value={plant.edible ? 'Yes' : 'No'} />
          <PlantDetailEntry label="Vegetable" value={plant.vegetable ? 'Yes' : 'No'} />
          <PlantDetailEntry label="Growth Rate" value={plant.growth_rate || 'N/A'} />
        </PlantDetailsSection>

        {/* Growing Conditions Section */}
        <PlantDetailsSection 
          title="Growing Conditions" 
          tooltip="Environmental requirements for optimal plant growth"
        >
          <PlantDetailEntry 
            label="Water Interval" 
            value={plant.water_interval ? `${plant.water_interval} days` : 'N/A'} 
          />
          <PlantDetailEntry label="Sunlight Requirements" value={plant.sunlight_requirements || 'N/A'} />
          <PlantDetailEntry label="Soil Type" value={plant.soil_type || 'N/A'} />
          <PlantDetailEntry 
            label="pH Range" 
            value={
              plant.ph_minimum && plant.ph_maximum 
                ? `${plant.ph_minimum} - ${plant.ph_maximum}` 
                : 'N/A'
            } 
          />
          <PlantDetailEntry 
            label="Temperature Range" 
            value={
              plant.min_temperature && plant.max_temperature 
                ? `${plant.min_temperature}°C - ${plant.max_temperature}°C` 
                : 'N/A'
            } 
          />
        </PlantDetailsSection>

        {/* Phenology Section */}
        <PlantDetailsSection 
          title="Phenology" 
          tooltip="Timing of seasonal biological events in the plant's life cycle"
        >
          <PlantDetailEntry label="Bloom Months" value={plant.bloom_months?.join(', ') || 'N/A'} />
          <PlantDetailEntry label="Fruit Months" value={plant.fruit_months?.join(', ') || 'N/A'} />
        </PlantDetailsSection>
      </div>
    </div>
  );

  /**
   * Renders the default state when no plant is selected
   * 
   * @returns {JSX.Element}
   */
  const renderDefaultState = () => (
    <h2 style={{
      fontSize: '40px', 
      color: 'black', 
      padding: '5px 10px', 
      borderRadius: '5px', 
      background: 'rgba(255, 253, 253, 0.6)'
    }}>
      Select a plant from the Sidebar
    </h2>
  );

  return (
    <>
      <NavBar buttonOptions={['back']} title="Catalog" onBack={() => { window.location.href = HOME_URL }} />
      <PlantSearchSideBar page="catalog" onPlantClick={handlePlantClick} />
      <div className='catalog-content'>
        {loading ? (
          <GridLoading />
        ) : (
          selectedPlant ? renderPlantDetails(selectedPlant) : renderDefaultState()
        )}
      </div>
    </>
  );
}

export default Catalog;