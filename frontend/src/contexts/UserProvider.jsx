import React, { createContext, useState } from 'react';
import useFetch from '../hooks/useFetch';
import { useEffect } from 'react';
import { useReducer } from 'react';
import { initialState, gardenReducer } from './gardenReducer';

const DEBUG = import.meta.env.VITE_DEBUG === 'true';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [gardens, dispatchGardens] = useReducer(gardenReducer, initialState);
    const [contextLoading, setContextLoading] = useState(true);

    // Optionally one could add mediation post fetch
    const { data: rawUser } = useFetch(import.meta.env.VITE_USER_PROFILE_API_URL);
    const { data: rawGardens } = useFetch(import.meta.env.VITE_GARDENS_API_URL);
    const [rawNotifications, setRawNotifications] = useState(null)
   
    // Populate states once fetch is complete
    useEffect(() => {
        if (rawUser) {
            console.log("User retrieved: ", rawUser.username);
            DEBUG && console.log(`RAW USER: `, rawUser);
            setUser(rawUser);
        }
    }, [rawUser]);

    useEffect(() => {
        if (rawGardens) {
            console.log("Gardens retrieved: ", rawGardens.map(garden => garden.name));
            DEBUG && console.log(`RAW GARDENS: `, rawGardens);
            let gardenIDs = Array(rawGardens.length);
            for (let [index, garden] of rawGardens.entries()){
                gardenIDs[index] = garden.id;
            }
            fetchNotifications(gardenIDs);
        }
    }, [rawGardens]);

    useEffect(() => {
        if (rawNotifications) {
            console.log("Notifications retrieved");
            DEBUG && console.log(`RAW NOTIFICATIONS: `, rawNotifications);
            if (rawNotifications.length !== rawGardens.length) throw new Error("Number of gardens and notifications do not match");
            const userGardens = rawGardens.map((garden, index) => {
                let gardenNotifications = rawNotifications[index].length > 0 ? rawNotifications[index][0]['notifications'] : [];
                return { notifications: gardenNotifications, ...garden };
            }); 
            dispatchGardens({ type: 'POPULATE', payload: userGardens });
        }
    }, [rawNotifications]);


    // For debugging purposes
    useEffect(() => {
        if (DEBUG) {
            console.log("GARDENS: ", gardens);
        }
    }, [gardens]);

    useEffect(() => {
        if (DEBUG) {
            console.log("USER: ", user);
        }
    }, [user]);

    const fetchNotifications = async (gardenIDs) => {
        if (!gardenIDs || !Array.isArray(gardenIDs) || gardenIDs.length === 0) {
          console.warn('Invalid or empty gardenIDs array');
          setRawNotifications([]);
          return;
        }
      
        try {
          const apiUrl = import.meta.env.VITE_NOTIFICATIONS_API_URL;
          if (!apiUrl) {
            throw new Error('VITE_NOTIFICATIONS_API_URL is not defined');
          }
      
          const fetchPromises = gardenIDs.map(async (gardenID) => {
            try {
              const response = await fetch(`${apiUrl}by_garden/?garden_id=${gardenID}`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                  'Content-Type': 'application/json',
                },
              });
      
              if (!response.ok) {
                throw new Error(`Failed to fetch notifications for garden ${gardenID}: ${response.status}`);
              }
      
              const data = await response.json();
              return data.notifications || [];
            } catch (error) {
              console.error(`Error fetching notifications for garden ${gardenID}:`, error);
              return [];
            }
          });
      
          const userNotifications = await Promise.all(fetchPromises);
          setRawNotifications(userNotifications);
        } catch (error) {
          console.error('Unexpected error in fetchNotifications:', error);
          setRawNotifications([]);
        } 
      };

    return (
        <UserContext.Provider
            value={{
                // // Username
                // username,
                // setUsername,
                // userId,
                
                // zipcode,
                // setZipcode,

                // weather,
                // setWeather,

                // // Plants list
                // plantsList,
                // setPlantsList,
                

                // // Notifications
                // notificationsList,
                // setNotifications,

                // Gardens
                gardens,
                // setGardens,
                user,
                dispatchGardens,
                contextLoading,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};


export default UserProvider;
