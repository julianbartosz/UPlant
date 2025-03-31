import React, { createContext, useContext, useEffect, useState } from 'react';


const UserContext = createContext(null);

export const useUser = () => {
    return useContext(UserContext);
};

export const UserProvider = ({ children }) => {

    const [user, setUser] = useState(null);
    const [gardens, setGardens] = useState(null); 

    // Renders for first time -> []
    useEffect(() => {
        console.log("RE_MOUNT")
        const fetchUser = async () => {
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate a delay of 500ms
            setUser({ username: "Gary Oak"}); 
        }
            
        // Simulate fetching user data
        const fetchGardens = async () => {

            // NOTE: Placeholder; will be part of garden data
            const cells1 = [
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
                { name: 'Garden 1', x: 5, y: 5, cells: cells1 },
                { name: 'Garden 2', x: 5, y: 5, cells: cells2 },
                { name: 'Garden 3', x: 5, y: 5, cells: cells3 }
            ];

            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate a delay of 500ms

            setGardens(gardens); // Set the fetched gardens
        };

        fetchGardens();
        fetchUser();

    }, []); 
    

    const handleRenameGarden = async (oldName, newName) => {

        if (!oldName || !newName || oldName === newName) {
            alert("Invalid garden names. Please provide valid names.");
            return;
        }

        if (gardens.some(garden => garden.name === newName)) {
            alert("A garden with the new name already exists. Please choose a different name.");
            return;
        }
        // Store the previous state in case we need to rollback
        const previousGardens = [...gardens];
        
        // Optimistically update UI
        setGardens(prevGardens =>
            prevGardens.map(garden =>
                garden.name === oldName ? { ...garden, name: newName } : garden
            )
        );

        try {
            const response = await fetch(`/api/gardens/${oldName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include' // Include credentials for authentication
                },
                body: JSON.stringify({ newName }),
            });
            if (!response.ok) {
                throw new Error("Failed to rename garden");
            }
            console.log(`Garden renamed from ${oldName} to ${newName} successfully.`);
        } catch (error) {
            console.error("Error renaming garden:", error);
            setGardens(previousGardens); // Rollback UI
            alert("Failed to rename garden. Please try again.");
            return;
        }
    };


    const handleUpdateGarden = async (updatedGarden) => {
        
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


    const handleDeleteGarden = async (gardenName) => {

        if (!gardenName || !gardens.some(garden => garden.name === gardenName)) {
            alert("Invalid garden name. Please provide a valid name.");
            return;
        }

        // Store the previous state in case we need to rollback
        const previousGardens = [...gardens];

        // Optimistically update UI
        const updatedGardens = gardens.filter(garden => garden.name !== gardenName);
        setGardens(updatedGardens);

        try {
            const response = await fetch(`/api/gardens/${gardenName}`, {
                method: 'DELETE',
                headers: { 
                    'Content-Type': 'application/json',
                    'credentials': 'include' 
                },
            });
            if (!response.ok) {
                throw new Error("Failed to delete garden");
            }
            console.log(`Garden ${gardenName} deleted successfully.`);

        } catch (error) {
            console.error("Error deleting garden:", error);
            setGardens(previousGardens); // Rollback UI
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
            setUser(previousUser); // Rollback UI
            alert("Failed to update user. Please try again.");
        }
    }

    const adjustCellRowTop = (garden, count = 1) => {
        setGardens(prevGardens =>
            prevGardens.map(g => {
                if (g.name !== garden.name) return g; // Keep other gardens unchanged
    
                const newRow = Array(5).fill(null);
                return {
                    ...g,
                    cells: [newRow, ...g.cells], // ✅ Add to the top
                    y: g.y + count // ✅ Increment Y properly
                };
            })
        );
    };
    
    const handleAddGarden = async (newGarden) => {

        if (!newGarden || !newGarden.name || newGarden.x <= 0 || newGarden.y <= 0) {
            alert("Invalid garden data. Please provide a valid name and dimensions.");
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
            setGardens(previousGardens); // Rollback UI
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
            adjustCellRowTop,
        
            }}>
            {children}
        </UserContext.Provider>
    );
};

export default UserProvider;
