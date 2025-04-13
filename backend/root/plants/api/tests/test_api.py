# backend/root/plants/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

class TrefleAPITest(APITestCase):
    def setUp(self):
        # Initialize the client provided by DRF
        self.client = APIClient()

# backend/root/plants/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

class TrefleAPITest(APITestCase):
    def setUp(self):
        # Initialize the client provided by DRF
        self.client = APIClient()

    def test_list_plants_endpoint(self):
        """
        Test the list_plants endpoint to ensure it returns properly formatted data
        that can be consumed by the frontend components.
        
        This endpoint is used by:
        - Plant search component in the CatalogPage
        - GardenDashboardPage search component when adding plants to garden cells
        """
        # STEP 1: Make request to the plants list endpoint
        url = reverse('list_plants')
        print(f"Calling API endpoint: {url}")
        response = self.client.get(url)
        
        # STEP 2: Verify HTTP response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK, 
                         "API should return 200 OK status")
        
        # STEP 3: Verify the overall response structure
        # Frontend expects these three main sections in the response
        self.assertIn('data', response.data, 
                      "Response should contain 'data' key with plant results")
        self.assertIn('links', response.data, 
                      "Response should contain 'links' key for pagination navigation")
        self.assertIn('meta', response.data, 
                      "Response should contain 'meta' key with pagination info")
        
        # STEP 4: Verify data contains plant entries
        plants = response.data.get('data', [])
        self.assertTrue(len(plants) > 0, 
                        "API should return at least one plant in the results")
        
        # STEP 5: Verify each plant has the required fields needed by the frontend
        first_plant = plants[0]
        print(f"Example plant data: {first_plant}")
        
        # Required fields for basic rendering in the frontend
        required_fields = ['id', 'common_name', 'scientific_name', 'slug']
        for field in required_fields:
            self.assertIn(field, first_plant, 
                          f"Plant data should contain '{field}' for frontend display")
        
        # STEP 6: Verify pagination information
        self.assertIn('total', response.data.get('meta', {}), 
                      "Response meta should contain total count for pagination")
        
        # STEP 7: Verify links for navigation
        links = response.data.get('links', {})
        self.assertTrue(any(key in links for key in ['self', 'first', 'next']), 
                        "Response should contain navigation links for pagination")

        print("✅ All list_plants endpoint checks passed successfully")

    def test_retrieve_plant_endpoint(self):
        # Get the list to find a valid plant slug
        list_url = reverse('list_plants')
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        data = list_response.data.get('data')
        self.assertTrue(len(data) > 0, "List endpoint should return at least one record")
        
        # Use the slug of the first plant for a detail call
        plant_slug = data[0]['slug']
        retrieve_url = reverse('retrieve_plant', args=[plant_slug])
        detail_response = self.client.get(retrieve_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIn('data', detail_response.data)
        # Check a specific field to confirm full data is returned
        self.assertIn('scientific_name', detail_response.data['data'])
