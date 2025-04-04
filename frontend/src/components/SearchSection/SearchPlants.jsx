// frontend/src/components/SearchSection/SearchPlants.jsx

import React, { useState, useEffect } from 'react';
import { useDrag } from 'react-dnd';
import './SearchPlants.css';

const SearchPlants = () => {

    const searchPlants = async (searchTerm) => {

        try {
            const response = await fetch(`/api/plants/search?term=${encodeURIComponent(searchTerm)}`, 
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'credentials': 'include' // Include credentials for authentication
                    }
                }
            );

            const data = await response.json();

        } catch (error) {
            console.error('Error fetching plants:', error);
        }
        
        // TODO: Setup search in backend
        // Dummy Data ->
        let plantslist = [
            { id: 19, icon: "🌽", name: "Corn" },
            { id: 29, icon: "🥦", name: "Broc" },
            { id: 39, icon: "🥕", name: "Carrot" },
            { id: 49, icon: "🌳", name: "Tree" },
            { id: 59, icon: "🍅", name: "Tomato" },
            { id: 69, icon: "🍆", name: "Eggplant" },
        ];

        if (false) {
            plantslist = data.results;
        }
            setFilteredPlants(plantslist)
        };

    const [searchTerm, setSearchTerm] = useState('');
    const [filteredPlants, setFilteredPlants] = useState({});

    const handleSearch = () => {
        console.log(`Searching for plants with term: ${searchTerm}`);
        searchPlants(searchTerm); // Fetch plants based on search term
    };
    
    return (
        <div>
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', marginBottom: '10px' }}>
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)} // Update input field
                    placeholder="Enter plant name..."
                    style={{ width: '150px', border: 'none', outline: 'none', fontSize: '16px' }}
                />
                <button 
                    onClick={handleSearch} 
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
                </button> {/* Trigger search */}
            </div>

            <PlantList plants={filteredPlants} />
        </div>
    );
};


const PlantList = ({ plants }) => {
    
    return (

        <div style={{ display: 'flex', flexWrap: 'wrap', width: '100%', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
            {plants && plants.length > 0 ? (
                plants.map((plant, index) => (
                    <div key={plant.id} style={{ fontSize: '21px', flex: '1 0 50%', boxSizing: 'border-box', padding: '10px' }}>
                        <PlantItem plant={plant} index={index} />
                    </div>
                ))
            ) : (
                <div style={{ fontSize: '18px', padding: '10px' }}></div>
            )}
        </div>

    );
};


const PlantItem = ({ plant, index }) => {

    const [, ref] = useDrag({
        type: 'PLANT',
        item: plant
    });

    return (
        <div ref={ref} className='plant-item' style={{ textAlign: 'center' }}>
            {plant.icon}
            <div style={{ fontSize: '14px', marginTop: '5px' }}>{plant.name}</div>
        </div>
    );
};
export default SearchPlants;