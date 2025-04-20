
import { useContext } from 'react';
import { UserContext } from '../contexts/UserProvider';

const useNotifications = () => {
    
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useNotifications must be used within a UserProvider");
    }

    const { notificationsList, setNotifications, notificationsListLoading, notificationsListError } = context;

   
    console.log("Notifications:", notificationsList);


    const mediateAddNotification = async (gardenIndex, notification) => {

        // {
        //     "garden": 1,          // ID of the specific garden
        //     "name": "Water plants",
        //     "type": "OT",         // Notification type (e.g., WA = Water)
        //     "subtype": "Morning", // Optional: Subtype (only required for "Other" type)
        //     "interval": 7         // Interval in days
        //   }
        if (gardenIndex < 0 || gardenIndex >= notificationsList.length) {
            alert("Invalid gardenIndex. Please provide a valid index.");
            return;
        }

        const updatedNotifications = notificationsList.map((garden, index) => 
            index === gardenIndex ? [...garden, notification] : garden
        );

        setNotifications(updatedNotifications);

        try {
            const response = await fetch(import.meta.env.VITE_NOTIFICATIONS_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'credentials': 'include'
                },
                body: JSON.stringify(notification),
            });

            if (!response.ok) {
                console.error("Add notification failed", response);
            }

            console.log(`Notification added successfully.`);
        } catch (error) {
            if (import.meta.env.VITE_USE_DUMMY_FETCH !== 'true') {
                console.error("Using dummy fetch, no rollback needed.")
            } else {
                console.error("Error adding notification:", error);
                setNotifications(notificationsList); // Rollback to previous state
                
            }
        }
    };

    const mediateDeleteNotification = async (gardenIndex, notificationIndex) => {
        if (
            gardenIndex < 0 || 
            gardenIndex >= notificationsList.length || 
            notificationIndex < 0 || 
            notificationIndex >= notificationsList[gardenIndex].length
        ) {
            alert("Invalid gardenIndex or notificationIndex. Please provide valid indices.");
            return;
        }

        const notificationId = notificationsList[gardenIndex][notificationIndex].id;

        const updatedNotifications = notificationsList.map((garden, index) => 
            index === gardenIndex ? garden.filter((_, i) => i !== notificationIndex) : garden
        );

        setNotifications(updatedNotifications);

        try {
            const response = await fetch(`${import.meta.env.VITE_NOTIFICATIONS_API_URL}/${notificationId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error("Failed to delete notification");
            }

            console.log(`Notification deleted successfully.`);
        } catch (error) {
            if (import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.error("Using dummy fetch, no rollback needed.");
                return;
            }
            console.error("Error deleting notification:", error);
            setNotifications(notificationsList); // Rollback to previous state
        }
    };

    return {
        notificationsList,
        setNotifications,
        notificationsListLoading,
        notificationsListError,
        mediateAddNotification,
        mediateDeleteNotification,
    };
};

export default useNotifications;