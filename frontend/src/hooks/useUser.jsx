import { useContext } from 'react';
import { UserContext } from '../contexts/UserProvider';

export const useUser = () => {
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useUser must be used within a UserProvider");
    }

    const { username, setUsername } = context;

    const updateUsername = async (newUsername) => {
        if (!newUsername) {
            alert("Invalid username. Please provide a valid username.");
            return;
        }

        try {
            const response = await fetch('/api/user/update-username', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include',
                },
                body: JSON.stringify({ username: newUsername }),
            });

            if (!response.ok) {
                throw new Error("Failed to update username");
            }

            setUsername((prevUser) => ({ ...prevUser, username: newUsername }));
            console.log("Username updated successfully.");
        } catch (error) {
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error updating username:", error);
            alert("Failed to update username. Please try again.");
        }
    };

    
    const mediateChangePassword = (oldPassword, newPassword, newPasswordConfirm) => {
        let result;
        let error;
        
        // Use an IIFE to handle the async operation
        (async () => {
            try {
                // Define the API endpoint
                const endpoint = '"http://localhost:8000/api/users/password/change/';
    
                // Prepare the request body
                const requestBody = {
                    current_password: oldPassword,
                    new_password: newPassword,
                    confirm_password: newPasswordConfirm,
                };
    
                // Make the API call
                const response = await fetch(endpoint, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        // 'Authorization': `Token ${localStorage.getItem('authToken')}`, // Add the user's auth token
                    },
                    body: JSON.stringify(requestBody),
                });
    
                if (response.ok) {
                    result = await response.json();
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to change password');
                }
            } catch (e) {
                error = e;
            }
        })();
    
        // Throw an error if one occurred
        if (error) throw error;
    
        // Return the result
        return result;
    }

    const mediateChangeUsername = (newUsername) => {
        if (!newUsername) {
            alert("Invalid username. Please provide a valid username.");
            return;
        }

        // Use an IIFE to handle the async operation
        (async () => {
            try {
                const response = await fetch('/me/profile/', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${localStorage.getItem('authToken')}`, // Add the user's auth token
                    },
                    body: JSON.stringify({ username: newUsername }),
                });

                if (!response.ok) {
                    setUsername((prevUser) => ({ ...prevUser, username: newUsername }));
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Failed to change username");
                }

                const result = await response.json();
                setUsername((prevUser) => ({ ...prevUser, username: result.username }));
                console.log("Username changed successfully.");
            } catch (error) {
                if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                    console.error("Using dummy fetch, no rollback needed.");
                    setUsername((prevUser) => ({ ...prevUser, username: newUsername }));
                    return;
                }
                console.error("Error changing username:", error);
                alert("Failed to change username. Please try again.");
            }
        })();
    };
    const deleteAccount = async () => {
        const confirmDelete = window.confirm("Are you sure you want to delete your account? This action cannot be undone.");

        if (!confirmDelete) {
            return;
        }

        try {
            const response = await fetch('/api/user/delete-account', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include',
                },
            });

            if (!response.ok) {
                throw new Error("Failed to delete account");
            }

            setUsername(null);

            console.log("Account deleted successfully.");
        } catch (error) {
            console.error("Error deleting account:", error);
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            alert("Failed to delete account. Please try again.");
        }
    };

    return {
        username,
        updateUsername,
       mediateChangePassword,
        mediateChangeUsername,
        deleteAccount,
    };
};

export default useUser;