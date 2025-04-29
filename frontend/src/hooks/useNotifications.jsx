import { useContext, useState, useEffect } from 'react';
import { UserContext } from '../contexts/UserProvider';

const useNotifications = () => {
    
    const context = useContext(UserContext);

    if (!context) {
        throw new Error("useNotifications must be used within a UserProvider");
    }

    const { gardens, notificationsList, setNotifications, notificationsListLoading, notificationsListError } = context;
    
    const [todaysNotifications, setTodaysNotifications] = useState(null);

    useEffect(() => {

        const determineReminders = () => {
            if (!notificationsList || !gardens) {
                console.log("Notifications or gardens not available");
                return;
            }

            const reminders = notificationsList && notificationsList.map(garden => {

                        return garden.filter(notification => {
                            const now = new Date();
                            console.log("Now:", notification.next_due);
                            const truncatedDate = notification.next_due.split('.')[0] + 'Z'; // Remove the fractional part
                            const nextDue = new Date(truncatedDate).setHours(0, 0, 0, 0);
                            console.log("Next due:", nextDue);
                            console.log("Now:", now);
                            return nextDue - now <= 24 * 60 * 60 * 1000 && nextDue > now;
                        })
                        .map((notification, index) => (
                    
                              {name: notification.name, plant_names: notification.plant_names, index: index}
                         
                        ));
                    });

                setTodaysNotifications(reminders);
            };

        determineReminders();
        
    }, [notificationsList]);
    

    console.log("Notifications:", notificationsList);

    const mediateAddNotification = async (gardenIndex, name, type, interval, plants, callback) => {
        const prevNotificationsList = [...notificationsList];
        const gardenNotifications = [...notificationsList[gardenIndex]];
        const gardenId = gardens[gardenIndex].id;
        console.log("Garden ID:", gardenId);
    
        const newNotification = {
            garden: `${gardenId}`,
            name: name,
            type: type, // Now correctly sent as a proper type code
            interval: interval,
            next_due: new Date(Date.now() + interval * 24 * 60 * 60 * 1000).toISOString(),
            plant_names: plants.map((plant) => plant.common_name),
        };
    
        // Validation checks
        if (!plants || plants.length === 0) {
            alert('Please select at least one plant.');
            return;
        }
    
        if (!name.trim()) {
            alert('Name cannot be empty.');
            return;
        }
    
        if (interval <= 0) {
            alert('Interval must be greater than 0.');
            return;
        }
    
        const isNameDuplicate = notificationsList[gardenIndex]?.some(
            (existingNotification) => existingNotification.name.toLowerCase() === name.toLowerCase()
        );
    
        if (isNameDuplicate) {
            alert('Name must be unique.');
            return;
        }
    
        // Update local state
        const updatedNotifications = notificationsList.map((garden, index) =>
            index === gardenIndex ? [...garden, newNotification] : garden
        );
        setNotifications(updatedNotifications);
        callback();
    
        try {
            // Create notification
            const notificationResponse = await fetch('http://localhost:8000/api/notifications/notifications/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newNotification),
            });
    
            if (!notificationResponse.ok) {
                console.error("Add notification failed", notificationResponse);
                setNotifications(prevNotificationsList); // Rollback
                return;
            }
    
            const notificationData = await notificationResponse.json();
            console.log("Notification data:", notificationData);
    
            // Process plants one at a time
            for (const plant of plants) {
                try {
                    const plantResponse = await fetch(`http://localhost:8000/api/notifications/notifications/${notificationData.id}/add_plant/`, {
                        method: 'POST', // Changed to POST as GET with body is non-standard
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ plant_id: plant.id }), // Adjust based on API requirements
                    });
    
                    if (!plantResponse.ok) {
                        console.error("Add plant failed", plantResponse);
                        continue; // Continue with next plant
                    }
    
                    const plantData = await plantResponse.json();
                    console.log("Plant association data:", plantData);
                    gardenNotifications.push(plantData);
                } catch (error) {
                    console.error("Error adding plant:", plant.id, error);
                    // Continue with next plant instead of failing entirely
                }
            }
    
            console.log("Garden notifications:", gardenNotifications);
            console.log("Plants:", plants);
            console.log("Plant IDs:", plants.map(plant => plant.id));
    
        } catch (error) {
            console.error("Error adding notification:", error);
            setNotifications(prevNotificationsList); // Rollback to previous state
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
            const response = await fetch(`${import.meta.env.VITE_NOTIFICATIONS_API_URL}${notificationId}/`, {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                }
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
        todaysNotifications,
        mediateAddNotification,
        mediateDeleteNotification,
    };
};

export default useNotifications;