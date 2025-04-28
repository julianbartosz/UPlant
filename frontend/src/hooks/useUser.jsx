import { useContext } from 'react';
import { UserContext } from '../contexts/UserProvider';

export const useUser = () => {
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useUser must be used within a UserProvider");
    }
    
    const { username, setUsername, userId } = context;

    const mediateDeleteAccount = async () => {

        if (!userId) {
            throw new Error('User ID is not available');
        }

        const confirmDelete = window.confirm('Are you sure you want to delete your account? This action cannot be undone.');

        if (!confirmDelete) {
            return;
        }

        const endpoint = `${import.meta.env.VITE_BACKEND_URL}/api/users/admin/users/${userId}/`; 
        try {
            const response = await fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Token 9811995a3db487b9cd8d772aac66cacbf6dc861c`,
                    'Content-Type': 'application/json',
                },
            });  

            if (!response.ok) {
                throw new Error('Failed to delete account');
            }
            alert('Account deleted successfully');
            window.location.href = import.meta.env.VITE_BACKEND_URL;
        } catch (error) {
            console.error('Error deleting account:', error);
            alert('Error deleting account. Please try again later.');
        }
    }

    return {
        username,
        setUsername,
        mediateDeleteAccount,
    };
};

export default useUser;