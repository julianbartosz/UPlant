import React, { createContext, useState } from 'react';
import useGet from '../hooks/useFetch';
import { useEffect } from 'react';
import {
    formatGardens,  
    formatNotificationsList,
} from './utils/formatting';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {

    const [user, setUser] = useState(null);
    const [username, setUsername] = useState(null);
    const [gardens, setGardens] = useState(null);
    const [notificationsList, setNotifications] = useState(null);
    const [plantsList, setPlantsList] = useState(null);
    const [zipcode, setZipcode] = useState(null);
    const [weather, setWeather] = useState(null);
     
    useEffect(() => {
            
            if (!gardens) return;

            const fetchNotifications = (lowerBoundIndex) => {
                let userNotifications = Array(gardens.length).fill(null);
                
                (async () => {
                    for (let i = 0; i < gardens.length; i++) {
                        if (i < lowerBoundIndex) {
                            userNotifications[i] = notificationsList[i];
                            continue;
                        }
                        try {
                            const response = await fetch(`${import.meta.env.VITE_NOTIFICATIONS_API_URL}by_garden/?garden_id=${gardens[i].id}`, {
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

            let bound;
            if (!notificationsList) {
                bound = 0;
            } else if (notificationsList.length === gardens.length) {
                bound = gardens.length - 1;
            } else if (notificationsList.length < gardens.length) {
                bound = notificationsList.length;
            } else {
                return;
            }

            fetchNotifications(bound);
       
    }, [gardens]);
    
    const {
        data: gardensData,
        error: gardensError,
        loading: gardensLoading,
    } = useGet(import.meta.env.VITE_GARDENS_API_URL);

    const {
        data: usersData,
        error: usersError,
        loading: usersLoading,
    } = useGet(import.meta.env.VITE_USER_PROFILE_API_URL);
    
    useEffect(() => {
        setUsername(usersData?.username);
        // setZipcode(usersData?.zipcode);
    }, [usersData]);

    useEffect(() => {
        if (gardensData) {
            const transformedGardens = formatGardens(gardensData);
            setGardens(transformedGardens);
        }
    }, [gardensData]);


    // useEffect(() => {
    //     const fetchWeather = async () => {
    //       try {
    //         const response = await fetch(
    //           `https://api.openweathermap.org/data/2.5/weather?zip=${zipcode}&units=metric&appid=${import.meta.env.OPEN_WEATHER_API_KEY}`,
    //         );
    //         if (!response.ok) {
    //           throw new Error("Failed to fetch weather data");
    //         }
    //         const data = await response.json();
    //         setWeather(data);
    //       } catch (err) {
    //         console.error("Failed to fetch weather:", err);
    //       }
    //     };
    //     if (zipcode) {
    //       fetchWeather();
    //     }
    
    
    //     }, [zipcode]);

    return (
        <UserContext.Provider
            value={{
                // Username
                username,
                setUsername,
                

                zipcode,
                setZipcode,

                weather,
                setWeather,

                // Plants list
                plantsList,
                setPlantsList,
                

                // Notifications
                notificationsList,
                setNotifications,

                // Gardens
                gardens,
                setGardens,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};


export default UserProvider;
