import { useEffect, useState } from 'react';
import { useContext } from 'react';
import { UserContext }  from '../contexts/UserProvider';

export const useGardens = () => {

    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useGardens must be used within a UserProvider");
    }

    const { gardens, setGardens, gardensLoading, gardensError, setNotifications } = context;

    // const mediateGridSizeChange = (index, newDims) => {
    //     const garden = gardens[index];

    //     if (!garden) {
    //         alert("Invalid garden data. Please provide valid gardens.");
    //         return;
    //     }

    //     const { x: newWidth, y: newHeight } = newDims;

    //     if (newWidth <= 0 || newHeight <= 0) {
    //         alert("Invalid dimensions. Please provide positive values for width and height.");
    //         return;
    //     }

    //     // Check if reducing dimensions would remove cells with plants
    //     if (newWidth < garden.x || newHeight < garden.y) {
    //         for (let row = newHeight; row < garden.y; row++) {
    //         for (let col = 0; col < garden.x; col++) {
    //             if (garden.cells[row]?.[col]) {
    //             alert("Cannot reduce height. Plants are present in the rows being removed.");
    //             return;
    //             }
    //         }
    //         }

    //         for (let col = newWidth; col < garden.x; col++) {
    //         for (let row = 0; row < garden.y; row++) {
    //             if (garden.cells[row]?.[col]) {
    //             alert("Cannot reduce width. Plants are present in the columns being removed.");
    //             return;
    //             }
    //         }
    //         }
    //     }

    //     // Adjust the garden dimensions
    //     const updatedCells = Array.from({ length: newHeight }, (_, row) =>
    //         Array.from({ length: newWidth }, (_, col) => garden.cells[row]?.[col] || null)
    //     );

    //     const updatedGarden = { ...garden, x: newWidth, y: newHeight, cells: updatedCells };

    //     mediateUpdateGarden(updatedGarden);

    // }
        
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
        console.log("Deleting garden...");
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
    const mediateAddGarden = async (setIndex) => {
        if (gardens.length >= 6) {
            alert("You cannot add more than 6 gardens. Or without premium at least.");
            return;
        }

        const x = parseInt(prompt("Enter the width (x) of the garden (max 10):"), 10);
        const y = parseInt(prompt("Enter the height (y) of the garden (max 10):"), 10);

        let name = prompt("Enter the name of the garden:");

        if (name && name.length > 10) {
            alert("Garden name cannot be more than 10 characters. Please try again.");
            return;
        }

        if (isNaN(x) || isNaN(y) || x <= 0 || y <= 0 || x > 10 || y > 10 || !name) {
            alert("Invalid input. Please provide valid dimensions (1-10) and a name.");
            return;
        }

        const cells = Array.from({ length: y }, () => Array(x).fill(null));
        const newGarden = { name: name, x: x, y: y, cells: cells };

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
        setNotifications(prevNotifications => [...prevNotifications, []]);
        setIndex(gardens.length);
        
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
        mediateAddGarden,
    };
};

export default useGardens;