/**
 * @file useFetch.jsx
 * @description A custom React hook for performing HTTP requests with support for memoized headers and body, 
 *              
 * 
 * @param {string} endpoint - The API endpoint to fetch data from.
 * @param {Object} [options={}] - Configuration options for the fetch request.
 * @param {string} [options.method='GET'] - HTTP method to use for the request.
 * @param {Object} [options.headers={}] - Additional headers to include in the request.
 * @param {Object|string|null} [options.body=null] - Request body to send with the request.
 * @param {boolean} [options.manual=false] - If true, disables automatic fetching and requires manual invocation of `refetch`.
 * @param {string} [options.credentials='include'] - Credentials mode for the request (e.g., 'include', 'same-origin').
 * 
 * @returns {Object} - An object containing the following properties:
 *   @property {any} data - The response data from the fetch request.
 *   @property {string|null} error - The error message, if an error occurred during the fetch.
 *   @property {boolean} loading - Indicates whether the fetch request is in progress.
 *   @property {Function} refetch - A function to manually trigger the fetch request.
 * 
 * @throws {Error} - Throws an error if the `endpoint` is not provided and `manual` is false.
 */
import { 
  useState, 
  useEffect, 
  useCallback, 
  useMemo 
} from 'react';
import { BASE_API, DEBUG } from '../constants';

const useFetch = (endpoint, options = {}) => {
  const {
    method = 'GET',
    headers = {},
    body = null,
    manual = false,
    credentials = 'include',
  } = options;

  if (!endpoint && !manual) {
    throw new Error('Endpoint prop is required');
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

    const url = new URL(endpoint, BASE_API);

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