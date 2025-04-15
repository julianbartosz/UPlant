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
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error updating username:", error);
            alert("Failed to update username. Please try again.");
        }
    };

    const updatePassword = async (newPassword) => {
        if (!newPassword) {
            alert("Invalid password. Please provide a valid password.");
            return;
        }

        try {
            const response = await fetch('/api/user/update-password', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include',
                },
                body: JSON.stringify({ password: newPassword }),
            });

            if (!response.ok) {
                throw new Error("Failed to update password");
            }

            console.log("Password updated successfully.");
        } catch (error) {
            console.error("Error updating password:", error);
            alert("Failed to update password. Please try again.");
        }
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
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            alert("Failed to delete account. Please try again.");
        }
    };

    return {
        username,
        updateUsername,
        updatePassword,
        deleteAccount,
    };
};

export default useUser;