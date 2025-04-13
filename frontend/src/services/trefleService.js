import axios from 'axios';

const API_BASE_URL = '/api/v1'; // This should be configurable for different environments

export const getPlantById = async (plantId) => {
  try {
    // backend endpoint instead
    const response = await axios.get(`${API_BASE_URL}/plants/${plantId}/`, {
      withCredentials: true
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching plant data:', error);
    throw error;
  }
};

export const getPlants = async (searchParams = {}) => {
  try {
    // Build query string from searchParams
    const queryString = Object.entries(searchParams)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
    
    const url = `${API_BASE_URL}/plants/${queryString ? `?${queryString}` : ''}`;
    const response = await axios.get(url, { withCredentials: true });
    return response.data;
  } catch (error) {
    console.error('Error fetching plants list:', error);
    throw error;
  }
};

export default {
  getPlantById,
  getPlants
};