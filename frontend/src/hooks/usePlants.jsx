import { useContext, useEffect, useState } from 'react';
import { UserContext } from '../contexts/UserProvider';

export const usePlants = () => {
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("usePlants must be used within a UserProvider");
    }
    
    const { 
        plantsList, 
        setPlantsList, 
        plantsListError,
        selectedPlant,
    } = context;
    
    const [loading, setLoading] = useState(false);

    const mediatePlantSearch = async (query) => {
        if (!query) {
            alert("Please provide a valid search query.");
            return;
        }
        setLoading(true);
        console.log("Searching for plants with query: ", query);

        try {
            
            const response = await fetch(`${import.meta.env.VITE_PLANT_SEARCH_API_URL}?q=${query}&limit=30`, {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            console.log("Response status:", response.status);

            if (!response.ok) {
                throw new Error("Failed to search plants");
            }

            const results = await response.json();
            setPlantsList(results.results.filter(plant => plant.common_name && plant.id && plant.family));
            console.log("Filtered plants list set successfully.");

        } catch (error) {
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error searching plants:", error);
            alert("Failed to search plants. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const mediatePlantRetrieval = async (plantId) => {
        if (!plantId) {
            alert("Invalid plant ID. Please provide a valid ID.");
            return;
        }
        
        setSelectedPlantLoading(true);

        try {
            const response = await fetch(`${import.meta.env.VITE_PLANT_RETRIEVAL_API_URL}${plantId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include',
                },
            });

            if (!response.ok) {
                throw new Error("Failed to retrieve plant details");
            }

            const plantDetails = await response.json();
            return plantDetails;
        } catch (error) {
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error retrieving plant details:", error);
            setSelectedPlantError(error);
            alert("Failed to retrieve plant details. Please try again.");
        }
    };

    return {
        plantsList,
        plantsListError,
        loading,
        mediatePlantSearch,
        mediatePlantRetrieval,
    };
};

export default usePlants;