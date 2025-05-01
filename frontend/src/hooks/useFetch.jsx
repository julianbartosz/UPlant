/**
 * @file useFetch.jsx
 * @description Custom React hook for fetching data from a given URL with flexible configuration.
 * @param {string} endpoint - The URL to fetch data from.
 * @param {Object} [options={}] - Fetch options.
 * @param {string} [options.method='GET'] - HTTP method (e.g., GET, POST, PUT).
 * @param {Object} [options.headers={}] - Custom headers for the request.
 * @param {Object|string|null} [options.body=null] - Request body (JSON object, string, or null).
 * @param {boolean} [options.manual=false] - If true, fetch is not triggered automatically.
 * @param {string} [options.credentials='include'] - Credentials mode for the request.
 * 
 * @returns {{ data: any, error: string | null, loading: boolean, refetch: Function }}
 *
 * @example
 * const { data, error, loading, refetch } = useFetch('/api/data', {
 *   method: 'POST',
 *   headers: { 'Custom-Header': 'value' },
 *   body: { key: 'value' }
 * });
 */

// imports
import { useState, useEffect, useCallback, useMemo } from 'react';

// environment variables
const DEBUG = import.meta.env.VITE_DEBUG === 'true';
const BASE_URL = import.meta.env.VITE_BACKEND_URL;

const useFetch = (endpoint, options = {}) => {
  const {
    method = 'GET',
    headers = {},
    body = null,
    manual = false,
    credentials = 'include',
  } = options;

  if (!endpoint && !manual) {
    throw new Error('ENDPOINT is required');
  }

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(!manual);

  // Memoize headers and body to prevent unnecessary re-renders
  const memoizedHeaders = useMemo(() => headers, [JSON.stringify(headers)]);
  const memoizedBody = useMemo(() => body, [JSON.stringify(body)]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const url = new URL(endpoint, BASE_URL);

    if (DEBUG) {
      console.log(`Request method: ${method}`);
      console.log(`Request headers:`, memoizedHeaders);
      console.log(`Request body:`, memoizedBody);
      console.log(`Request URL: ${url}`);
    }

    try {
      const fetchOptions = {
        method,
        credentials,
        headers: {
          'Authorization': `Token ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...memoizedHeaders,
        },
      };

      if (memoizedBody) {
        fetchOptions.body = typeof memoizedBody === 'string' ? memoizedBody : JSON.stringify(memoizedBody);
      }

      const response = await fetch(url, fetchOptions);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      return result;
    } catch (err) {
      if (DEBUG) {
        console.error('Fetch error:', err);
      }
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint, method, memoizedHeaders, memoizedBody, credentials]);

  useEffect(() => {
    if (!manual) {
      fetchData();
    }
  }, [fetchData, manual]);

  return { data, error, loading, refetch: fetchData };
};

export default useFetch;