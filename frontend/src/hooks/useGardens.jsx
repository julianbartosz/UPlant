import { useEffect, useState } from 'react';
import { useContext } from 'react';
import { UserContext }  from '../contexts/UserProvider';

export const useGardens = () => {

    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useGardens must be used within a UserProvider");
    }

    const { gardens, setGardens, gardensLoading, gardensError } = context;

    const mediateRenameGarden = async (index) => {
        const garden = gardens[index];

        if (!garden) {
            alert("Invalid garden data. Please provide valid gardens.");
            return;
        }

        const newGardenName = prompt(`Enter a new name for the garden: ${garden.name}`);

        if (!newGardenName) {
            alert("Invalid garden name. Please provide a valid name.");
            return;
        }

        const updatedGardens = gardens.map((g, i) => 
            i === index ? { ...g, name: newGardenName } : g
        );

        setGardens(updatedGardens);

        try {
            const response = await fetch(`/api/gardens/${garden.name}/rename`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'credentials': 'include'
            },
            body: JSON.stringify({ newName: newGardenName }),
            });

            if (!response.ok) {
            throw new Error("Failed to rename garden");
            }

            console.log(`Garden renamed to ${newGardenName} successfully.`);
        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error renaming garden:", error);
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            setGardens(previousGardens); // Rollback UI
            alert("Failed to rename garden. Please try again.");
        }
    };
    
    
    const mediateUpdateGarden = async (updatedGarden, sync=true) => {
        
        if (!updatedGarden) {
            alert("Invalid garden data. Please provide valid gardens.");
            return;
        }

        // Store the previous state in case we need to rollback
        const previousGardens = [...gardens];

        // Optimistically update UI
        setGardens(prevGardens =>
            prevGardens.map(garden =>
                garden.name === updatedGarden.name ? updatedGarden : garden
            )
        )

        if (!sync) {
            return;
        }


        try {
            const response = await fetch('/api/gardens', {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'credentials': 'include' 
                },
                body: JSON.stringify(updatedGarden),
            });

            if (!response.ok) {
                throw new Error("Failed to update gardens");
            }

        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error updating gardens:", error);
            setGardens(previousGardens); // Rollback UI
            alert("Failed to update gardens. Please try again.");
        }

    }


    const mediateDeleteGarden = async (index) => {
        const garden = gardens[index];

        if (!garden) {
            alert("Invalid garden data. Please provide valid gardens.");
            return;
        }

        const confirmDelete = window.confirm(`Are you sure you want to delete the garden: ${garden.name}?`);

        if (!confirmDelete) {
            return;
        }

        // Store the previous state in case we need to rollback
        const previousGardens = [...gardens];

        // Optimistically update UI
        setGardens(prevGardens => prevGardens.filter((_, i) => i !== index));

        try {
            const response = await fetch(`/api/gardens/${garden.name}`, {
                method: 'DELETE',
                headers: { 
                    'Content-Type': 'application/json',
                    'credentials': 'include' 
                },
            });

            if (!response.ok) {
                console.log("Response not ok");
            }

            console.log(`Garden "${garden.name}" deleted successfully.`);
        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error deleting garden:", error);
            setGardens(previousGardens); // Rollback UI
            alert("Failed to delete garden. Please try again.");
        }
       
    };

    const mediateAddGarden = async () => {

        const x = parseInt(prompt("Enter the width (x) of the garden:"), 10);
        const y = parseInt(prompt("Enter the height (y) of the garden:"), 10);
        const name = prompt("Enter the name of the garden:");

        if (isNaN(x) || isNaN(y) || x <= 0 || y <= 0 || !name) {
            alert("Invalid input. Please provide valid dimensions and a name.");
            return;
        }

        const cells = Array.from({ length: y }, () => Array(x).fill(null));
        const newGarden = { name, x, y, cells };

        if (!newGarden || !newGarden.name || newGarden.x <= 0 || newGarden.y <= 0) {
            alert("Invalid garden data. Please provide a valid name and dimensions.");
            return;
        }

        if (gardens.some(garden => garden.name === newGarden.name)) {
            alert("A garden with this name already exists. Please choose a different name.");
            return;
        }

        // Store the previous state in case we need to rollback
        const previousGardens = [...gardens];
    
        // Optimistically update UI
        setGardens(prevGardens => [...prevGardens, newGarden]);
        
        try {
            const response = await fetch('/api/gardens', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'credentials': 'include' 
                },
                body: JSON.stringify(newGarden),
            });
    
            if (!response.ok) {
                throw new Error("Failed to save garden");
            }

            // If API assigns an ID or modifies data, update with the real data
            const savedGarden = await response.json();

            setGardens(prevGardens =>
                prevGardens.map(garden =>
                    garden === newGarden ? savedGarden : garden
                )
            );
    
        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error saving garden:", error);
            setGardens(previousGardens); // Rollback UI
            alert("Failed to save garden. Please try again.");
        }
    };

    return {
        gardens,
        setGardens,
        gardensError,
        gardensLoading,
        mediateRenameGarden,
        mediateUpdateGarden,
        mediateDeleteGarden,
        mediateAddGarden
    };
};