from django.test import TestCase
from unittest.mock import patch, MagicMock
from services.trefle_service import list_plants, TrefleAPIError
import json

class TrefleServiceTest(TestCase):
    
    def setUp(self):
        # Sample API response data for mocking
        self.mock_rose_data = {
            "data": [
                {"id": 1, "common_name": "Rose", "slug": "rosa-test", "scientific_name": "Rosa test"},
                {"id": 2, "common_name": "Wild Rose", "slug": "rosa-wild", "scientific_name": "Rosa wild"}
            ],
            "links": {"self": "/api/v1/plants", "next": "/api/v1/plants?page=2"},
            "meta": {"total": 10}
        }
        
        self.mock_trees_data = {
            "data": [
                {"id": 3, "common_name": "Oak", "slug": "quercus-test", "scientific_name": "Quercus test"},
                {"id": 4, "common_name": "Maple", "slug": "acer-test", "scientific_name": "Acer test"}
            ],
            "links": {"self": "/api/v1/plants", "next": "/api/v1/plants?page=2"},
            "meta": {"total": 15}
        }

    @patch('services.trefle_service._make_request_query_auth')
    def test_filtering(self, mock_request):
        # Set up mock to return sample data
        mock_request.return_value = self.mock_rose_data
        
        # Test filtering by common_name
        result = list_plants(filters={"common_name": "rose"})
        
        # Verify the API call args
        call_args = mock_request.call_args[0]
        url = call_args[0]
        params = call_args[1]
        
        # Check URL is correct
        self.assertEqual(url, "https://trefle.io/api/v1/plants")
        
        # Check filter parameters are correctly passed
        self.assertEqual(params["page"], 1)
        self.assertEqual(params["common_name"], "rose")
        
        # Note: Token appears to be handled internally by _make_request_query_auth
        # rather than being passed directly in the params
        
        # Verify the returned data
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["data"][0]["common_name"], "Rose")
        
        # Print what happened for clarity
        print("\nFiltering Test:")
        print(f"Filter requested: common_name=rose")
        print(f"URL requested: {url}")
        print(f"Query params: {params}")
        print(f"Results returned: {len(result['data'])} plants")

    @patch('services.trefle_service._make_request_query_auth')
    def test_pagination(self, mock_request):
        # Set up different responses for different pages
        mock_request.side_effect = [self.mock_rose_data, self.mock_trees_data]
        
        # Test page 1
        result_page1 = list_plants(page=1)
        self.assertEqual(len(result_page1["data"]), 2)
        self.assertEqual(result_page1["data"][0]["common_name"], "Rose")
        
        # Test page 2
        result_page2 = list_plants(page=2)
        self.assertEqual(len(result_page2["data"]), 2)
        self.assertEqual(result_page2["data"][0]["common_name"], "Oak")
        
        # Verify the API was called with correct page parameters
        call_args_list = mock_request.call_args_list
        self.assertEqual(call_args_list[0][0][1]["page"], 1)
        self.assertEqual(call_args_list[1][0][1]["page"], 2)
        
        print("\nPagination Test:")
        print(f"Page 1 requested: {call_args_list[0][0][1]}")
        print(f"Page 2 requested: {call_args_list[1][0][1]}")
        print(f"Page 1 results: {len(result_page1['data'])} plants")
        print(f"Page 2 results: {len(result_page2['data'])} plants")

    @patch('services.trefle_service._make_request_query_auth')
    def test_ordering(self, mock_request):
        mock_request.return_value = self.mock_rose_data
        
        # Test ordering parameters
        list_plants(order={"common_name": "asc", "year": "desc"})
        
        # Verify the API was called with correct ordering parameters
        expected_order = "common_name:asc,year:desc"
        self.assertEqual(mock_request.call_args[0][1]["order"], expected_order)
        
        print("\nOrdering Test:")
        print(f"Order requested: common_name:asc,year:desc")
        print(f"URL params: {mock_request.call_args[0][1]}")

    @patch('services.trefle_service._make_request_query_auth')
    def test_range_filtering(self, mock_request):
        mock_request.return_value = self.mock_rose_data
        
        # Test range parameters
        list_plants(range={"year": "1800-1900", "height": "5-10"})
        
        # Verify the API was called with correct range parameters
        expected_range = "year:1800-1900,height:5-10"
        self.assertEqual(mock_request.call_args[0][1]["range"], expected_range)
        
        print("\nRange Filtering Test:")
        print(f"Range requested: year:1800-1900,height:5-10")
        print(f"URL params: {mock_request.call_args[0][1]}")

    @patch('services.trefle_service._make_request_query_auth')
    def test_all_parameters_combined(self, mock_request):
        mock_request.return_value = self.mock_rose_data
        
        # Test combining all parameter types
        result = list_plants(
            filters={"common_name": "rose", "edible": "true"},
            page=3,
            order={"common_name": "desc"},
            range={"height": "1-5"}
        )
        
        # Verify the API call parameters
        call_args = mock_request.call_args[0][1]
        self.assertEqual(call_args["page"], 3)
        self.assertEqual(call_args["common_name"], "rose")
        self.assertEqual(call_args["edible"], "true")
        self.assertEqual(call_args["order"], "common_name:desc")
        self.assertEqual(call_args["range"], "height:1-5")
        
        print("\nCombined Parameters Test:")
        print(f"All parameters: {call_args}")
        print(f"Results: {len(result['data'])} plants")