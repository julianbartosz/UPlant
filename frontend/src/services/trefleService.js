// frontend/src/services/trefleService.js

/**
 * Fetches the list of plants from the Django REST API endpoint.
 * @returns {Promise<Object>} The JSON response containing the list of plants, links, and metadata.
 */
export async function listPlants() {
    try {
      // Fetch from the relative API endpoint
      const response = await fetch('/api/v1/plants');
      if (!response.ok) {
        throw new Error(`Error fetching plant list: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error in listPlants:", error);
      throw error;
    }
  }
  
  /**
   * Fetches details for a specific plant using its id or slug.
   * @param {string} id - The unique identifier or slug of the plant.
   * @returns {Promise<Object>} The JSON response containing the plant details.
   */
  export async function retrievePlant(id) {
    try {
      // Build the endpoint URL dynamically using the plant id (or slug)
      const response = await fetch(`/api/v1/plants/${id}`);
      if (!response.ok) {
        throw new Error(`Error fetching plant with id ${id}: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error in retrievePlant:", error);
      throw error;
    }
  }
  