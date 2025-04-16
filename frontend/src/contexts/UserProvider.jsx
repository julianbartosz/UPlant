import React, { createContext, useState } from 'react';
import useFetch from '../hooks/useFetch';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {

    const {
        data: plantsList,
        loading: plantsListLoading,
        error: plantsListError,
        setData: setPlantsList,
    } = useFetch(import.meta.env.VITE__PLANTS_API_URL);

    const {
        data: username,
        loading: usernameLoading,
        error: usernameError,
        setData: setUsername,
    } = useFetch(import.meta.env.VITE__USERNAME_API_URL);

    const {
        data: notifications,
        loading: notificationsLoading,
        error: notificationsError,
        setData: setNotifications,
    } = useFetch(import.meta.env.VITE__NOTIFICATIONS_API_URL);

    const {
        data: gardens,
        loading: gardensLoading,
        error: gardensError,
        setData: setGardens,
    } = useFetch(import.meta.env.VITE__GARDENS_API_URL);

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
                notifications,
                setNotifications,
                notificationsLoading,
                notificationsError,

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
