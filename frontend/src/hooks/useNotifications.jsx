
import { useContext } from 'react';
import { UserContext } from '../contexts/UserProvider';

const useNotifications = () => {
    
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useNotifications must be used within a UserProvider");
    }

    const { notifications, setNotifications, notificationsLoading, notificationsError } = context;

   
    console.log("Notifications:", notifications);

    const mediateAddNotification = async (gardenIndex, notification) => {
        if (gardenIndex < 0 || gardenIndex >= notifications.length) {
            alert("Invalid gardenIndex. Please provide a valid index.");
            return;
        }

        const updatedNotifications = notifications.map((garden, index) => 
            index === gardenIndex ? [...garden, notification] : garden
        );

        setNotifications(updatedNotifications);

        try {
            const response = await fetch(`/api/notifications`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include'
                },
                body: JSON.stringify({ gardenIndex, notification }),
            });

            if (!response.ok) {
                console.error("Add notification failed", response);
            }

            console.log(`Notification added successfully.`);
        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH !== 'true') {
                console.error("Using dummy fetch, no rollback needed.")
            } else {
                console.error("Error adding notification:", error);
                setNotifications(notifications); // Rollback to previous state
                
            }
        }
    };

    const mediateDeleteNotification = async (gardenIndex, notificationIndex) => {
        if (
            gardenIndex < 0 || 
            gardenIndex >= notifications.length || 
            notificationIndex < 0 || 
            notificationIndex >= notifications[gardenIndex].length
        ) {
            alert("Invalid gardenIndex or notificationIndex. Please provide valid indices.");
            return;
        }

        const updatedNotifications = notifications.map((garden, index) => 
            index === gardenIndex ? garden.filter((_, i) => i !== notificationIndex) : garden
        );

        setNotifications(updatedNotifications);

        try {
            const response = await fetch(`/api/notifications`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include'
                },
                body: JSON.stringify({ gardenIndex, notificationIndex }),
            });

            if (!response.ok) {
                throw new Error("Failed to delete notification");
            }

            console.log(`Notification deleted successfully.`);
        } catch (error) {
            if (import.meta.env.VITE__USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error deleting notification:", error);
            setNotifications(notifications); // Rollback to previous state
        }


    };

    return {
        notifications,
        setNotifications,
        notificationsLoading,
        notificationsError,
        mediateAddNotification,
        mediateDeleteNotification,
    };
};

export default useNotifications;