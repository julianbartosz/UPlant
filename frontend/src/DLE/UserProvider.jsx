import { createContext, useState, useEffect, useReducer } from 'react';
import { initialState, gardenReducer } from './gardenReducer';
import { useFetch } from '../hooks';

// environment variables
const DEBUG = import.meta.env.VITE_DEBUG === 'true';
console.log("DEBIGGING:", DEBUG);

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [gardens, dispatch] = useReducer(gardenReducer, initialState);
    const [contextLoading, setContextLoading] = useState(true);
    
    /* ======= Fetching users, profile, gardens, and notifications ======= */
    const { data: rawUser } = useFetch('/api/users/me/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    });

    const { data: rawGardens } = useFetch('/api/gardens/gardens/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    });
    
    const { data: rawNotifications } = useFetch('/api/notifications/notifications/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    });
    
    /* ======= Populating states ======= */
    useEffect(() => {
        if (rawUser && !user && contextLoading) {
            console.log("Fetched user profile, populating user state");
            // Remove sensitive data from user object
            setUser({ ...rawUser, email: undefined, zipcode: undefined });
        }
    }, [rawUser]);

    useEffect(() => {
        if (rawNotifications && rawGardens && contextLoading) {
            console.log("RAW Notifications:", rawNotifications);
            const processedGardens = rawGardens.map((garden, index) => {
                return {...garden, notifications: rawNotifications[index] || [] };
            });
            dispatch({ type: 'POPULATE', payload: processedGardens });
            setContextLoading(false);
        }
    }, [rawNotifications, rawGardens]);
    
    /* ======= Debugging ======= */
    useEffect(() => {
        if (DEBUG) {
            if (user && gardens && !contextLoading) {
                console.log("✅ UserContext has been successfully initialized ✅");
                console.log("UserContext state:", {
                    user,
                    gardens,
                    contextLoading,
                });
            }
        }
    }, [gardens, user, contextLoading]);

    useEffect(() => {
        if (DEBUG) {
            if (rawNotifications) {
                console.log("Fetched users notifications: ", rawNotifications);
            } 
        }
    }, [rawNotifications]);

    useEffect(() => {
        if (DEBUG) {
            if (rawGardens) {
                console.log("Fetched users gardens: ", rawGardens);
            } 
        }
    }, [rawGardens]);
    
    useEffect(() => {
        if (DEBUG) {
            if (rawUser) {
                console.log("Fetched user profile: ", rawUser);
            } 
        }
    }, [rawUser]);

    return (
        <UserContext.Provider
            value={{
                // Garden state
                gardens,
                dispatch,

                // User state
                user,
                
                // Process states
                contextLoading,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};


export default UserProvider;
