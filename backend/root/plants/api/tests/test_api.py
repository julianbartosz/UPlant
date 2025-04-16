# backend/root/plants/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.test import TestCase
from unittest.mock import patch, MagicMock
import json
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

class RetrievePlantEndpointTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        
        # Updated mock plant detail with ALL required fields
        self.mock_plant_detail = {
            "data": {
                "id": 42,
                "common_name": "Test Plant",
                "slug": "test-plant",
                "scientific_name": "Testus plantus",
                "family": "Testaceae",
                "image_url": "https://example.com/image.jpg",
                # Add the missing required fields:
                "status": "accepted",
                "rank": "species",
                "genus_id": 123,
                "genus": "Testus",
                "family_common_name": "Test Family",
                "edible": False,
                "synonyms": [],
                "links": {}
            }
        }

    @patch('plants.api.views.retrieve_plants')
    def test_retrieve_plant_detailed(self, mock_retrieve_plants):
        """Test the retrieve_plant endpoint with detailed diagnostics"""
        # Configure mock to return our test data
        mock_retrieve_plants.return_value = self.mock_plant_detail
        
        # Make request to the retrieve endpoint
        url = reverse('retrieve_plant', args=['test-plant'])
        print(f"\nTesting endpoint: {url}")
        response = self.client.get(url)
        
        # Print actual response data for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response content type: {type(response.content)}")
        print(f"Raw response content: {response.content.decode()}")
        
        # Try to parse the response as JSON
        try:
            response_data = json.loads(response.content)
            print(f"Parsed JSON data: {json.dumps(response_data, indent=2)}")
            
            # Check the response structure
            print("\nAnalyzing response structure:")
            if isinstance(response_data, dict):
                top_level_keys = list(response_data.keys())
                print(f"Top-level keys: {top_level_keys}")
                
                # Check if data is nested or at top level
                if 'data' in top_level_keys:
                    print("Response has nested 'data' field")
                    data_keys = list(response_data['data'].keys())
                    print(f"Keys inside data: {data_keys}")
                else:
                    print("Response has plant data at top level")
                    # Check for key fields expected in plant data
                    for key in ['id', 'scientific_name', 'common_name', 'slug']:
                        print(f"Contains '{key}': {key in top_level_keys}")
            else:
                print(f"Response is not a dictionary but {type(response_data)}")
                
        except json.JSONDecodeError:
            print("Response is not valid JSON")
        
        # Now run the actual test assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Compare the expected and actual structure
        print("\nComparing expected vs actual structure:")
        expected_structure = self.mock_plant_detail  # The data we mocked
        try:
            # Get the actual response structure
            actual_data = response.data
            print(f"Type of response.data: {type(actual_data)}")
            
            # Check if data matches our expectations
            if 'data' in actual_data:
                print("Response correctly has a 'data' key")
                
                # Check if expected fields are in the response
                plant_data = actual_data['data']
                for key in ['id', 'scientific_name', 'common_name', 'slug']:
                    if key in plant_data:
                        print(f"✅ '{key}' is present in response data")
                    else:
                        print(f"❌ '{key}' is missing from response data")
            else:
                print("❌ Response doesn't have a 'data' key")
                # Check if fields are at top level instead
                for key in ['id', 'scientific_name', 'common_name', 'slug']:
                    if key in actual_data:
                        print(f"⚠️ '{key}' is at top-level instead of inside 'data'")
        except Exception as e:
            print(f"Error analyzing response: {e}")

        # UPDATED ASSERTIONS to match actual API behavior
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check for required fields directly at the top level (not nested)
        for key in ['id', 'scientific_name', 'common_name', 'slug']:
            self.assertIn(key, response.data, f"Response should contain '{key}' field")