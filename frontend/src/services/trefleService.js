import axios from 'axios';

const TREFLE_API_URL = 'https://trefle.io/api/v1/plants';
const TREFLE_API_TOKEN = 'KbMe4aVuGQwIhB0NCKCYcDUPlt56qDTFsnQmEA6hQPU'; // Replace with your Trefle API token

export const getPlantById = async (plantId) => {
  try {
    const response = await axios.get(`${TREFLE_API_URL}/${plantId}`, {
      headers: {
        Authorization: `Bearer ${TREFLE_API_TOKEN}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching plant data:', error);
    throw error;
  }
};

export default getPlantById;
