# backend/root/plants/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from plants.models import Plant, PlantChangeRequest
import json

User = get_user_model()

class TrefleAPITest(APITestCase):
    """Tests for the Trefle API integration endpoints"""
    
    def setUp(self):
        # Initialize the client provided by DRF
        self.client = APIClient()

    @patch('plants.api.views.list_plants')
    def test_list_plants_endpoint(self, mock_list_plants):
        """
        Test the list_plants endpoint to ensure it returns properly formatted data
        that can be consumed by the frontend components.
        """
        # Mock the API response
        mock_list_plants.return_value = {
            "data": [
                {
                    "id": 123,
                    "common_name": "Test Plant",
                    "scientific_name": "Testus plantus",
                    "slug": "test-plant",
                    "family": "Testaceae",
                    "genus": "Testus",
                    "status": "accepted",
                    "rank": "species",
                    "genus_id": 1,
                    "image_url": "https://example.com/plant.jpg"
                }
            ],
            "links": {
                "self": "/api/v1/plants",
                "next": "/api/v1/plants?page=2"
            },
            "meta": {
                "total": 100
            }
        }
        
        # STEP 1: Make request to the plants list endpoint
        url = reverse('plants_api:trefle-list-plants')
        response = self.client.get(url)
        
        # STEP 2: Verify HTTP response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK, 
                         "API should return 200 OK status")
        
        # STEP 3: Verify the overall response structure
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
        
        # Required fields for basic rendering in the frontend
        required_fields = ['id', 'common_name', 'scientific_name', 'slug']
        for field in required_fields:
            self.assertIn(field, first_plant, 
                          f"Plant data should contain '{field}' for frontend display")
        
        # STEP 6: Verify pagination information
        self.assertIn('total', response.data.get('meta', {}), 
                      "Response meta should contain total count for pagination")

    @patch('plants.api.views.retrieve_plants')
    def test_retrieve_plant_endpoint(self, mock_retrieve_plants):
        """Test the retrieve_plant endpoint returns formatted plant details"""
        # Mock the API response
        mock_retrieve_plants.return_value = {
            "data": {
                "id": 42,
                "common_name": "Test Plant",
                "slug": "test-plant",
                "scientific_name": "Testus plantus",
                "family": "Testaceae",
                "image_url": "https://example.com/image.jpg",
                "status": "accepted",
                "rank": "species",
                "genus_id": 123,
                "genus": "Testus",
                "family_common_name": "Test Family",
                "edible": False,
                "synonyms": []
            },
            "links": {}
        }
        
        # Make request to the retrieve endpoint
        url = reverse('plants_api:trefle-retrieve-plant', args=['test-plant'])
        response = self.client.get(url)
        
        # Verify response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('data', response.data, "Response should contain 'data' key")
        
        # Verify plant details are present
        plant_data = response.data['data']
        for field in ['id', 'common_name', 'scientific_name', 'slug']:
            self.assertIn(field, plant_data, f"Plant data should contain '{field}'")


class PlantViewSetTest(APITestCase):
    """Tests for the Plant ViewSet API endpoints"""
    
    def setUp(self):
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin', 
            email='admin@example.com', 
            password='password',
            is_staff=True,
            role='Admin'
        )
        self.mod_user = User.objects.create_user(
            username='moderator', 
            email='mod@example.com', 
            password='password',
            role='Moderator'
        )
        self.regular_user = User.objects.create_user(
            username='user', 
            email='user@example.com',
            password='password',
            role='User'
        )
        self.another_user = User.objects.create_user(
            username='another', 
            email='another@example.com',
            password='password',
            role='User'
        )
        
        # Create a mock Trefle plant (admin-maintained)
        self.trefle_plant = Plant.objects.create(
            common_name="Trefle Plant",
            scientific_name="Treflus plantus",
            slug="trefle-plant",
            api_id=123,
            is_user_created=False,
            water_interval=7,
            created_by=self.admin_user
        )
        
        # Create a user-created plant
        self.user_plant = Plant.objects.create(
            common_name="User Plant",
            scientific_name="Userus plantus",
            slug="user-plant",
            is_user_created=True,
            water_interval=3,
            created_by=self.regular_user
        )
        
        # Initialize the client
        self.client = APIClient()
    
    def test_list_plants_unauthenticated(self):
        """Test that unauthenticated users can list plants"""
        url = reverse('plants_api:plant-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_create_plant_as_admin(self):
        """Test that admins can create plants directly"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('plants_api:plant-list')
        data = {
            'common_name': 'Admin Plant',
            'scientific_name': 'Adminus plantus',
            'slug': 'admin-plant',
            'water_interval': 5
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Plant.objects.count(), 3)
    
    def test_create_plant_as_user_fails(self):
        """Test that regular users cannot create plants directly"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-list')
        data = {
            'common_name': 'User Direct Plant',
            'scientific_name': 'Userus directus',
            'slug': 'user-direct-plant',
            'water_interval': 5
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Plant.objects.count(), 2)
    
    def test_create_custom_plant_as_user(self):
        """Test that users can create custom plants via the custom endpoint"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-create-custom')
        data = {
            'common_name': 'Custom User Plant',
            'water_interval': 4,
            'detailed_description': 'My custom plant description'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Plant.objects.count(), 3)
        self.assertTrue(response.data['is_user_created'])
        self.assertEqual(response.data['created_by'], self.regular_user.id)
    
    def test_update_own_plant_as_user(self):
        """Test that users can update their own plants"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-user-update', args=[self.user_plant.id])
        data = {
            'common_name': 'Updated User Plant',
            'water_interval': 5
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_plant.refresh_from_db()
        self.assertEqual(self.user_plant.common_name, 'Updated User Plant')
        self.assertEqual(self.user_plant.water_interval, 5)
    
    def test_update_another_users_plant_fails(self):
        """Test that users cannot update plants created by others"""
        self.client.force_authenticate(user=self.another_user)
        url = reverse('plants_api:plant-user-update', args=[self.user_plant.id])
        data = {
            'common_name': 'Hijacked Plant',
            'water_interval': 10
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user_plant.refresh_from_db()
        self.assertEqual(self.user_plant.common_name, 'User Plant')  # Unchanged
    
    def test_admin_can_update_any_plant(self):
        """Test that admins can update any plant"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('plants_api:plant-detail', args=[self.user_plant.id])
        data = {
            'common_name': 'Admin Updated Plant',
            'water_interval': 6
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_plant.refresh_from_db()
        self.assertEqual(self.user_plant.common_name, 'Admin Updated Plant')
    
    def test_direct_update_trefle_plant_as_user_fails(self):
        """Test that users cannot update Trefle plants directly"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-user-update', args=[self.trefle_plant.id])
        data = {
            'common_name': 'Hacked Trefle Plant',
            'water_interval': 10
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.trefle_plant.refresh_from_db()
        self.assertEqual(self.trefle_plant.common_name, 'Trefle Plant')  # Unchanged


class PlantChangeRequestTest(APITestCase):
    """Tests for the Plant Change Request API endpoints"""
    
    def setUp(self):
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin', 
            email='admin@example.com', 
            password='password',
            is_staff=True,
            role='Admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', 
            email='user@example.com',
            password='password',
            role='User'
        )
        
        # Create a mock Trefle plant
        self.trefle_plant = Plant.objects.create(
            common_name="Trefle Plant",
            scientific_name="Treflus plantus",
            slug="trefle-plant",
            api_id=123,
            is_user_created=False,
            water_interval=7,
            created_by=self.admin_user
        )
        
        # Create a change request
        self.change_request = PlantChangeRequest.objects.create(
            plant=self.trefle_plant,
            user=self.regular_user,
            field_name='water_interval',
            old_value='7',
            new_value='5',
            reason='This plant needs less water',
            status='PENDING'
        )
        
        # Initialize the client
        self.client = APIClient()
    
    def test_submit_change_request(self):
        """Test that users can submit change requests for Trefle plants"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-submit-change', args=[self.trefle_plant.id])
        data = {
            'field_name': 'common_name',
            'new_value': 'Better Name',
            'reason': 'This name is more accurate'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlantChangeRequest.objects.count(), 2)
        
        # Verify the plant itself hasn't changed yet
        self.trefle_plant.refresh_from_db()
        self.assertEqual(self.trefle_plant.common_name, 'Trefle Plant')  # Unchanged
    
    def test_user_cannot_submit_change_for_admin_only_field(self):
        """Test that users cannot request changes to admin-only fields"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-submit-change', args=[self.trefle_plant.id])
        data = {
            'field_name': 'scientific_name',  # Admin-only field
            'new_value': 'Hackus plantus',
            'reason': 'I want to change this'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PlantChangeRequest.objects.count(), 1)  # No new request created
    
    def test_approve_change_request_as_admin(self):
        """Test that admins can approve change requests"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('plants_api:change-request-approve', args=[self.change_request.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the change request status is updated
        self.change_request.refresh_from_db()
        self.assertEqual(self.change_request.status, 'APPROVED')
        self.assertEqual(self.change_request.reviewer, self.admin_user)
        
        # Verify the plant has been updated
        self.trefle_plant.refresh_from_db()
        self.assertEqual(self.trefle_plant.water_interval, 5)  # Value changed from 7 to 5
    
    def test_reject_change_request_as_admin(self):
        """Test that admins can reject change requests"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('plants_api:change-request-reject', args=[self.change_request.id])
        data = {
            'notes': 'This change is incorrect'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the change request status is updated
        self.change_request.refresh_from_db()
        self.assertEqual(self.change_request.status, 'REJECTED')
        self.assertEqual(self.change_request.reviewer, self.admin_user)
        self.assertEqual(self.change_request.review_notes, 'This change is incorrect')
        
        # Verify the plant has NOT been updated
        self.trefle_plant.refresh_from_db()
        self.assertEqual(self.trefle_plant.water_interval, 7)  # Unchanged
    
    def test_user_cannot_approve_change_requests(self):
        """Test that regular users cannot approve change requests"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:change-request-approve', args=[self.change_request.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify the change request status is unchanged
        self.change_request.refresh_from_db()
        self.assertEqual(self.change_request.status, 'PENDING')
        
        # Verify the plant has NOT been updated
        self.trefle_plant.refresh_from_db()
        self.assertEqual(self.trefle_plant.water_interval, 7)  # Unchanged


class PlantStatisticsTest(APITestCase):
    """Tests for the Plant Statistics API endpoint"""
    
    def setUp(self):
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin', 
            email='admin@example.com', 
            password='password',
            is_staff=True,
            role='Admin'
        )
        self.regular_user = User.objects.create_user(
            username='user', 
            email='user@example.com',
            password='password',
            role='User'
        )
        
        # Create plants
        Plant.objects.create(
            common_name="Trefle Plant",
            scientific_name="Treflus plantus",
            slug="trefle-plant",
            api_id=123,
            is_user_created=False,
            water_interval=7,
            is_verified=True,
            created_by=self.admin_user
        )
        
        Plant.objects.create(
            common_name="User Plant",
            scientific_name="Userus plantus",
            slug="user-plant",
            is_user_created=True,
            water_interval=3,
            created_by=self.regular_user
        )
        
        # Create change requests
        PlantChangeRequest.objects.create(
            plant=Plant.objects.get(slug="trefle-plant"),
            user=self.regular_user,
            field_name='water_interval',
            old_value='7',
            new_value='5',
            status='PENDING'
        )
        
        # Initialize the client
        self.client = APIClient()
    
    def test_statistics_as_admin(self):
        """Test that admins can see comprehensive statistics"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('plants_api:plant-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify admin-specific stats are present
        self.assertIn('total_plants', response.data)
        self.assertIn('user_created_plants', response.data)
        self.assertIn('trefle_plants', response.data)
        self.assertIn('verified_plants', response.data)
        self.assertIn('pending_changes', response.data)
        
        # Verify counts are correct
        self.assertEqual(response.data['total_plants'], 2)
        self.assertEqual(response.data['user_created_plants'], 1)
        self.assertEqual(response.data['trefle_plants'], 1)
        self.assertEqual(response.data['verified_plants'], 1)
        self.assertEqual(response.data['pending_changes'], 1)
    
    def test_statistics_as_user(self):
        """Test that regular users see limited statistics"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('plants_api:plant-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user-specific stats are present
        self.assertIn('total_plants', response.data)
        self.assertIn('your_plants', response.data)
        self.assertIn('your_pending_changes', response.data)
        
        # Verify admin-only stats are not present
        self.assertNotIn('approved_changes', response.data)
        self.assertNotIn('rejected_changes', response.data)
        
        # Verify counts are correct
        self.assertEqual(response.data['total_plants'], 2)
        self.assertEqual(response.data['your_plants'], 1)
        self.assertEqual(response.data['your_pending_changes'], 1)