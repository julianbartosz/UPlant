import { 
     createContext, 
     useState,
     useEffect, 
     useReducer, 
     useMemo 
    } from 'react';
import { initialState, gardensReducer } from './reducers/gardensReducer';
import { useFetch } from '../hooks';
import { DEBUG } from '../constants';

// display DEBUG status in console
if (DEBUG) {
    console.log("DEBUG mode is ON");
} else {
    console.log("DEBUG mode is OFF");
}

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [gardens, dispatch] = useReducer(gardensReducer, initialState);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Fetch user profile
    const { data: rawUser, error: userError } = useFetch('/api/users/me/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Fetch gardens and notifications
    const { data: rawGardens, error: gardensError } = useFetch('/api/gardens/gardens/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    const { data: rawNotifications, error: notificationsError } = useFetch('/api/notifications/notifications/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Fetch notifications counts for nav bar bell
    const { 
        data: notificationsCounts, 
        error: countsError,
        refetch: refreshCounts
    } = useFetch('/api/notifications/instances/counts/', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    useEffect(() => {

        if (userError || gardensError || notificationsError || countsError) {
            console.error("Error fetching data:", userError, gardensError, notificationsError);
            setError('Failed to fetch data');
            setLoading(false);
            return;
        }
        if (DEBUG) {
            console.log("Data fetch successful");
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
        notificationsError,
        countsError,
        notificationsCounts
    ]);

    useEffect(() => {
        if (rawUser && !user && loading) {
            if (DEBUG) {
                console.log("RAW USER:", rawUser);
            }
            console.log("Fetched user profile, populating user state");
            // Remove sensitive data from user object
            setUser({ ...rawUser, email: undefined, zipcode: undefined });
        }
    }, [rawUser]);

    useEffect(() => {
        if (rawNotifications && rawGardens && loading && gardens === null) {
            if (DEBUG) {
                console.log("RAW Notifications:", rawNotifications);
                console.log("RAW Gardens:", rawGardens);
            }

            const processedGardens = rawGardens.map((garden) => {
                return {
                    ...garden,
                    notifications: rawNotifications.filter(
                        (notification) => notification['garden'] === garden.id
                    ),
                };
            });
            dispatch({ type: 'POPULATE', payload: processedGardens });
            setLoading(false);

            if (DEBUG) {
                console.log("Processed Gardens:", processedGardens);
            }
        }
    }, [rawNotifications, rawGardens]);

    const contextValue = useMemo(
        () => ({
            gardens,
            dispatch,
            user,
            setUser,
            loading,
            error,
            refreshCounts,
            notificationsCounts,
        }),
        [gardens, dispatch, user, loading, error, refreshCounts, notificationsCounts]
    );

    return (
        <UserContext.Provider value={contextValue}>
            {children}
        </UserContext.Provider>
    );
};

export default UserProvider;