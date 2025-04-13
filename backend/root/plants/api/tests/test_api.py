# backend/root/plants/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

class TrefleAPITest(APITestCase):
    def setUp(self):
        # Initialize the client provided by DRF
        self.client = APIClient()

    def test_list_plants_endpoint(self):
        # Reverse lookup for list endpoint (as configured in urls.py)
        url = reverse('list_plants')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify that the response includes expected keys
        self.assertIn('data', response.data)
        self.assertIn('links', response.data)
        self.assertIn('meta', response.data)

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
