import { useContext } from 'react';
import { UserContext }  from '../contexts/UserProvider';
import { MAXSIZE_GARDEN } from '../constants';

export const useGardens = () => {

    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useGardens must be used within a UserProvider");
    }

    const { gardens, setGardens, gardensLoading, gardensError, setNotifications } = context;

    const mediateGridSizeChange = (axis, change, edge, gardenName) => {
        const gardenIndex = gardens.findIndex(garden => garden.name === gardenName);
        const newGarden = { ...gardens[gardenIndex] };

        if (axis === 'x') {
            if (newGarden.x + change > MAXSIZE_GARDEN) {
                alert(`Cannot resize: Maximum garden width of ${MAXSIZE_GARDEN} reached.`);
                return;
            }

            if (newGarden.x + change < 1) {
                alert('Cannot resize: Garden width cannot be smaller than 1.');
                return;
            }

            if (change < 0) {
                const columnIndex = edge === 'left' ? 0 : newGarden.x - 1;
                const hasPlant = newGarden.cells.some(row => row[columnIndex] !== null);
                if (hasPlant) {
                    alert('Cannot resize: Plants would be deleted.');
                    return;
                }
            }

            newGarden.x += change;
            if (edge === 'left') {
                newGarden.cells.forEach(row => change > 0 ? row.unshift(null) : row.shift());
            } else if (edge === 'right') {
                newGarden.cells.forEach(row => change > 0 ? row.push(null) : row.pop());
            }

        } else if (axis === 'y') {
            if (newGarden.y + change > MAXSIZE_GARDEN) {
                alert(`Cannot resize: Maximum garden height of ${MAXSIZE_GARDEN} reached.`);
                return;
            }

            if (newGarden.y + change < 1) {
                alert('Cannot resize: Garden height cannot be smaller than 1.');
                return;
            }

            if (change < 0) {
                const rowIndex = edge === 'top' ? 0 : newGarden.y - 1;
                const hasPlant = newGarden.cells[rowIndex].some(cell => cell !== null);
                if (hasPlant) {
                    alert('Cannot resize: Plants would be deleted.');
                    return;
                }
            }

            newGarden.y += change;
            if (edge === 'top') {
                change > 0 ? newGarden.cells.unshift(Array(newGarden.x).fill(null)) : newGarden.cells.shift();
            } else if (edge === 'bottom') {
                change > 0 ? newGarden.cells.push(Array(newGarden.x).fill(null)) : newGarden.cells.pop();
            }
        }

        mediateUpdateGarden(newGarden, false);
    };
        
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
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error renaming garden:", error);
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
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
            const response = await fetch(import.meta.env.VITE_GARDENS_API_URL, {
                method: 'PATCH',
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
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
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
            const response = await fetch(`${import.meta.env.VITE_GARDENS_API_URL}/${garden.id}`, {
                method: 'DELETE',
                headers: { 
                    'Content-Type': 'application/json',

                },
                'credentials': 'include' 
            });

            if (!response.ok) {
                console.log("Response not ok");
                setNotifications(prevNotifications => prevNotifications.filter((_, i) => i !== index));
            }

            console.log(`Garden "${garden.name}" deleted successfully.`);
        } catch (error) {
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                // Handle dummy fetch scenario
                console.error("Using dummy fetch, no rollback needed.");
                setNotifications(prevNotifications => prevNotifications.filter((_, i) => i !== index));
                return;
            }
            console.error("Error deleting garden:", error);
            setGardens(previousGardens); // Rollback UI
            alert("Failed to delete garden. Please try again.");
        }
       
    };
    const mediateAddGarden = async (setIndex) => {

        // const newGarden = {
        //     name: "My New Garden", // Name of the garden
        //     size_x: 10,            // Width of the garden grid
        //     size_y: 5              // Height of the garden grid
        // };
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
        const newGardenReq = { name: name, size_x: x, size_y: y};

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

        const url = 'https://your-api-url.com/api/gardens/'; // Replace with your actual API URL
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}` // Include the user's token for authentication
                },
                body: JSON.stringify(requestBody),
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
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
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
        mediateGridSizeChange,
    };
};

export default useGardens;