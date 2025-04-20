import React, { createContext, useState } from 'react';
import useFetch from '../hooks/useFetch';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {

    const {
        data: plantsList,
        loading: plantsListLoading,
        error: plantsListError,
        setData: setPlantsList,
    } = useFetch(import.meta.env.VITE_PLANTS_API_URL);

    const {
        data: username,
        loading: usernameLoading,
        error: usernameError,
        setData: setUsername,
    } = useFetch(import.meta.env.VITE_USERNAME_API_URL);

    const {
        data: notificationsList,
        loading: notificationsListLoading,
        error: notificationsListError,
        setData: setNotifications,
    } = useFetch(import.meta.env.VITE_NOTIFICATIONS_API_URL);

    const {
        data: gardens,
        loading: gardensLoading,
        setLoading: setGardensLoading,
        error: gardensError,
        setData: setGardens,
    } = useFetch(import.meta.env.VITE_GARDENS_API_URL);

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
                plantsListLoading,
                plantsListError,

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
                notificationsListLoading,
                notificationsListError,

                // Gardens
                gardens,
                setGardens,
                gardensLoading,

                gardensError,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};


export default UserProvider;
