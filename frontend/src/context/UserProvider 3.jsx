import { createContext, useState, useEffect, useReducer, useMemo } from 'react';
import { initialState, gardensReducer } from './reducers';
import { useFetch } from '../hooks';

// environment variables
const DEBUG = import.meta.env.VITE_DEBUG === 'true';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [gardens, dispatch] = useReducer(gardensReducer, initialState);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    /* ======= Fetching users, profile, gardens, and notifications ======= */
    const { data: rawUser, error: userError } = useFetch('/api/users/me/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    });

    const { data: rawGardens, error: gardensError } = useFetch('/api/gardens/gardens/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    });
    
    const { data: rawNotifications, error: notificationsError } = useFetch('/api/notifications/notifications/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    });
    
    /* ======= Populating states ======= */
    useEffect(() => {

        if (userError || gardensError || notificationsError) {
            console.error("Error fetching data:", userError, gardensError, notificationsError);
            setError('Failed to fetch data');
            setLoading(false);
            return;
        }

    }, [
        rawUser, 
        rawGardens, 
        rawNotifications, 
        gardens, 
        user,
        loading, 
        error,
        userError,  
        gardensError, 
        notificationsError
    ]);

    useEffect(() => {
        if (rawUser && !user && loading) {
            console.log("Fetched user profile, populating user state");
            // Remove sensitive data from user object
            setUser({ ...rawUser, email: undefined, zipcode: undefined });
        }

    }, [rawUser]);  
    
    useEffect(() => {
        if (rawNotifications && rawGardens && loading && gardens === null) {
            const processedGardens = rawGardens.map(garden => {
                return {...garden, notifications: rawNotifications.filter(notification => notification['garden'] === garden.id)};
            });
            dispatch({ type: 'POPULATE', payload: processedGardens });
            setLoading(false);
        }
    }
    , [rawNotifications, rawGardens]);

    
    const contextValue = useMemo(
        () => ({
          gardens,
          dispatch,
          user,
          loading,
          error,
        }),
        [gardens, dispatch, user, loading, error]
      );

    return (
        <UserContext.Provider value={contextValue}>
            {children}
        </UserContext.Provider>
    );
};

export default UserProvider;