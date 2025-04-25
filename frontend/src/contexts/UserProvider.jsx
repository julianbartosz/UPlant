import React, { createContext, useState } from 'react';
import useGet from '../hooks/useFetch';
import { useEffect } from 'react';
import {formatGardens,  formatNotificationsList } from './utils/formatting';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {

    const [token, setToken] = useState("4c1775be909a3873ee6c23104d433adaf4cbde29");

    // Update localStorage whenever the token changes
    useEffect(() => {
        if (token) {
            localStorage.setItem('token', token);
        }
    }, [token]);

    const [gardens, setGardens] = useState(null);
    const [notificationsList, setNotifications] = useState(null);
    const [plantsList, setPlantsList] = useState(null);

    useEffect(() => {
        if (gardens && !notificationsList) {
            
            const fetchNotifications = () => {
                let userNotifications = Array(gardens.length).fill(null);
                (async () => {
                    for (let i = 0; i < gardens.length; i++) {
                        try {
                            const response = await fetch(`http://localhost:8000/api/notifications/notifications/by_garden/?garden_id=${gardens[i].id}`, {
                                method: 'GET',
                                credentials: 'include',
                                headers: {
                                    'Content-Type': 'application/json',
                                }
                            });
                            const data = await response.json();
                            console.log("Notifications data:", data);
                            userNotifications[i] = data;
                        } catch (error) {
                            console.error("Error fetching notifications:", error);
                        }
                    }
                    console.log("User notifications:", userNotifications);
                const formattedNotifications = formatNotificationsList(userNotifications);
                console.log("Formatted notifications:", formattedNotifications);
                setNotifications(formattedNotifications);
                })();
            };
        
            fetchNotifications();
        }
    }
    , [gardens, notificationsList]);


    const {
        data: username,
        loading: usernameLoading,
        error: usernameError,
        setData: setUsername,
    } = useGet(import.meta.env.VITE_USERNAME_API_URL);

    const {
        data: gardensData,
        loading: gardensLoading,
        error: gardensError,
    } = useGet(import.meta.env.VITE_GARDENS_API_URL);

    useEffect(() => {
        console.log("Gardens data:", gardensData);
        if (gardensData) {
            const transformedGardens = formatGardens(gardensData);
            console.log("Transformed gardens:", transformedGardens);
            setGardens(transformedGardens);
        }
    }, [gardensData]);

    const [selectedPlant, setSelectedPlant] = useState(null);
    const [selectedPlantLoading, setSelectedPlantLoading] = useState(false);
    const [selectedPlantError, setSelectedPlantError] = useState(null);

    return (
        <UserContext.Provider
            value={{
                // Username
                username,
                setUsername,
                usernameLoading,
                usernameError,

                // Plants list
                plantsList,
                setPlantsList,

                // Selected plant (manual)
                selectedPlant,
                setSelectedPlant,
                selectedPlantLoading,
                setSelectedPlantLoading,
                selectedPlantError,
                setSelectedPlantError,

                // Notifications
                notificationsList,
                setNotifications,

                // Gardens
                gardens,
                setGardens,
                gardensLoading,

                gardensError,
                token,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};


export default UserProvider;
