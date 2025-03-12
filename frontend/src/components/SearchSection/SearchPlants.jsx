// frontend/src/components/SearchSection/SearchPlants.jsx

import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import './SearchPlants.css';

const fetchPlants = (searchTerm) => {

//     try {
//         const response = await fetch('/api/plants/{searchTerm}');
//         const data = await response.json();
//         return data;
//     } catch (error) {
//         console.error('Error fetching plants:', error);
//         return [];
//     }
// };

// TODO: Retrieve Plants matching search
    let plantslist = [
        { id: 19, name: "🌽", description: "Corn" },
        { id: 29, name: "🥦", description: "Broc" },
        { id: 39, name: "🥕", description: "Carrot" },
        { id: 49, name: "🌳", description: "Tree" },
    ];

    return plantslist;
};


const SearchPlants = ({ username }) => {


    const [searchTerm, setSearchTerm] = useState('');
    const [filteredPlants, setFilteredPlants] = useState(fetchPlants(searchTerm));

    useEffect(() => {
        if (searchTerm) {
            setFilteredPlants(fetchPlants(searchTerm))
        }
    }, [searchTerm]);

    const handleSearch = (event) => {
        const term = event.target.value.toLowerCase();
        setSearchTerm(term);
    };
    
    return (
        <div>
            <input
                type="text"
                placeholder="🔍 Search plants"
                value={searchTerm}
                onChange={handleSearch}
                className="search-input"
                style={{ color: 'black', backgroundColor: 'white', marginBottom: '10px' }}  
            />

            <PlantList plants={filteredPlants} />
        </div>
    );
};


const PlantList = ({ plants }) => {
    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', width: '100%', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
            {plants.map((plant, index) => (
                
                <div key={plant.id} style={{ fontSize: '21px', flex: '1 0 50%', boxSizing: 'border-box', padding: '10px' }}>
                    <PlantItem plant={plant} index={index} />
                </div>
            ))}
        </div>
    );
};


const PlantItem = ({ plant, index }) => {
    const [, ref] = useDrag({
        type: 'PLANT',
        item: plant
    });

    return (
        <div ref={ref} className='plant-item'>
            {plant.name}
        </div>
    );
};
export default SearchPlants;