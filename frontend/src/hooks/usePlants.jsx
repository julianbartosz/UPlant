import { useContext, useEffect } from 'react';
import { UserContext } from '../contexts/UserProvider';

export const usePlants = () => {
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("usePlants must be used within a UserProvider");
    }
    
    const { 
        plantsList, 
        setPlantsList, 
        plantsListLoading, 
        setPlantsListLoading,
        plantsListError,
        setPlantsListError,
        selectedPlant,
        selectedPlantLoading,
        selectedPlantError,
        setSelectedPlantLoading,
        setSelectedPlantError,
        setSelectedPlant,
        
    } = context;
    

    const mediatePlantSearch = async (query) => {
        if (!query) {
            alert("Please provide a valid search query.");
            return;
        }

        setPlantsListLoading(true);

        try {
            const response = await fetch(`/api/plants/search?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include',
                },
            });

            if (!response.ok) {
                throw new Error("Failed to search plants");
            }

            const results = await response.json();
            setPlantsList(results);
        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            setPlantsListError(error);
            console.error("Error searching plants:", error);
            alert("Failed to search plants. Please try again.");
        }
    };

    const mediatePlantRetrieval = async (plantId) => {
        if (!plantId) {
            alert("Invalid plant ID. Please provide a valid ID.");
            return;
        }
        
        setSelectedPlantLoading(true);

        try {
            const response = await fetch(`/api/plants/${plantId}`, {
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
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
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
        plantsListLoading,
        plantsListError,
        selectedPlant,
        selectedPlantLoading,
        selectedPlantError,
        mediatePlantSearch,
        mediatePlantRetrieval,
    };
};

export default usePlants;