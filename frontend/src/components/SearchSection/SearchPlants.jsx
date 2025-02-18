import React, { useState } from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import './SearchPlants.css';

const SearchPlants = ({ plants }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredPlants, setFilteredPlants] = useState(plants);

    const handleSearch = (event) => {
        const term = event.target.value.toLowerCase();
        setSearchTerm(term);
        setFilteredPlants(plants.filter(plant => plant.name.toLowerCase().includes(term)));
    };

    return (
        <div className="search-plants-container">
            <input
                type="text"
                placeholder="Search plants..."
                value={searchTerm}
                onChange={handleSearch}
                className="search-input"
            />
            <DndProvider backend={HTML5Backend} >
                <PlantList plants={filteredPlants} />
            </DndProvider>
        </div>
    );
};

const PlantList = ({ plants }) => {
    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', width: '100%', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
            {plants.map((plant, index) => (
                <div key={plant.id} style={{ flex: '1 0 50%', boxSizing: 'border-box', padding: '10px' }}>
                    <PlantItem plant={plant} index={index} />
                </div>
            ))}
        </div>
    );
};

const PlantItem = ({ plant, index }) => {
    const [, ref] = useDrag({
        type: 'PLANT',
        item: { id: plant.id, index }
    });

    return (
        <div ref={ref} className='plant-item'>
            {plant.name}
        </div>
    );
};
export default SearchPlants;