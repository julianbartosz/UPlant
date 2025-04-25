/**
 * @file useFetch.jsx
 * @description Custom React hook for fetching data from a given URL.
 * @param {string} url
 * @param {Object} [options={}] 
 * @param {string} [options.method='GET'] 
 * @param {Object} [options.headers={}] 
 * @param {Object} [options.body=null]
 * 
 * @returns {{ data: any, error: string | null }}
 *
 * @example
 * const { data, error, loading } = useFetch('/api/data');
 */

import { useState, useEffect } from "react";
import { DummyFetch } from "../debugger";

const useGet = (url) => {

    if (!url) {
        throw new Error("URL is required");
    }

    const allowedEndpoints = import.meta.env.VITE_ALLOWED_ENDPOINTS?.split(',') || [];
    const isValidEndpoint = allowedEndpoints.some(endpoint => url.startsWith(endpoint));

    if (!isValidEndpoint) {
        throw new Error("The provided URL is not among the allowed endpoints");
    }

    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);

            if (import.meta.env.VITE_GARDENS_API_URL !== url && import.meta.env.VITE_USE_DUMMY_FETCH === 'true') {
                console.log("Using dummy fetch");
                console.log("Dummy fetch URL:", url);
                const dummyData = await DummyFetch(url);
                console.log("Dummy data:", dummyData);

                setData(dummyData.data);
                setLoading(false);
                return;
            }
      

            try {
                const response = await fetch(url,  {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        // 'Authorization': `Token ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',

                    }
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const result = await response.json();
                setData(result);

                setLoading(false);


            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        
        fetchData();
    }, []);

    return { data, setData, error, loading };
};

export default useGet;