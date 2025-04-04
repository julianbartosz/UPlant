// frontend/src/contexts/ProtectedRoute.jsx

import React, { createContext, useContext, useEffect, useState } from 'react';

const UserContext = createContext(null);

export const useUser = () => {
    const { user, handleUpdateUser } = useContext(UserContext);
    return { user, handleUpdateUser };
};

export const useGardens = () => {

    const { 
        gardens,
        handleAddGarden, 
        handleUpdateGarden, 
        handleDeleteGarden, 
        handleRenameGarden, 
        setGardens
    } = useContext(UserContext);

    return {
        gardens,
        handleAddGarden,
        handleUpdateGarden,
        handleDeleteGarden,
        handleRenameGarden,
        setGardens
    };
};

export const UserProvider = ({ children }) => {
    
    const [user, setUser] = useState(null);
    const [gardens, setGardens] = useState(null); 

    useEffect(() => {
        const fetchUser = async () => {
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate a delay of 500ms
            setUser({ username: "Gary Oak"}); 
        }
        // Simulate fetching user data
        const fetchGardens = async () => {
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate a delay of 500ms
            // NOTE: Placeholder; will be part of garden data
            const cells1 = [
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
            ];
            const cells2 = [
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
            ];
            const cells3 = [
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
                Array(5).fill(null),
            ];
            // TODO: Retrieve Gardens
            let gardens = [
                { name: 'Garden 1', x: 5, y: 10, cells: cells1 },
                { name: 'Garden 2', x: 5, y: 5, cells: cells2 },
                { name: 'Garden 3', x: 5, y: 5, cells: cells3 }
            ];

            gardens = gardens.map(garden => {
                if (garden.cells.length !== garden.y || garden.cells.some(row => row.length !== garden.x)) {
                    console.warn(`Garden "${garden.name}" has mismatched dimensions. Adjusting to match x: ${garden.x}, y: ${garden.y}.`);
                    const adjustedCells = Array.from({ length: garden.y }, () =>
                        Array(garden.x).fill(null)
                    );
                    return { ...garden, cells: adjustedCells };
                }
                return garden;
            });

            setGardens(gardens); 
        };

        fetchGardens();
        fetchUser();

    }, []); 
    

    const handleRenameGarden = async (index) => {

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
            console.error("Error renaming garden:", error);
            // setGardens(previousGardens); // Rollback UI
            alert("Failed to rename garden. Please try again.");
        }
    };

    
    const handleUpdateGarden = async (updatedGarden, sync=true) => {
        
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
            console.error("Error updating gardens:", error);
            // setGardens(previousGardens); // Rollback UI
            alert("Failed to update gardens. Please try again.");
        }
    }


    const handleDeleteGarden = async (index) => {
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
            console.error("Error deleting garden:", error);
            // setGardens(previousGardens); // Rollback UI
            alert("Failed to delete garden. Please try again.");
        }
       
    };

    const handleUpdateUser = async (updatedUser) => {

        if (!updatedUser || !updatedUser.username) {
            alert("Invalid user data. Please provide a valid username.");
            return;
        }
        // Store the previous state in case we need to rollback
        const previousUser = { ...user };
        // Optimistically update UI
        setUser(updatedUser);

        try {
            const response = await fetch('/api/user', {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'credentials': 'include' 
                },
                body: JSON.stringify(updatedUser),
            });

            if (!response.ok) {
                throw new Error("Failed to update user");
            }

        } catch (error) {
            console.error("Error updating user:", error);
            // setUser(previousUser); // Rollback UI
            alert("Failed to update user. Please try again.");
        }
    }

    const handleAddGarden = async () => {

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
            console.error("Error saving garden:", error);
            // setGardens(previousGardens); // Rollback UI
            alert("Failed to save garden. Please try again.");
        }
    };
    
    return (
        <UserContext.Provider value=
        {{ 
            user, 
            gardens, 
            handleAddGarden, 
            handleUpdateGarden, 
            handleDeleteGarden, 
            handleRenameGarden, 
            handleUpdateUser,
            setGardens
            }}>
            {children}
        </UserContext.Provider>
    );
};

export default UserProvider;