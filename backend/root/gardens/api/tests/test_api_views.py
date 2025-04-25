# backend/root/gardens/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from gardens.models import Garden, GardenLog
from plants.models import Plant
from django.utils import timezone

User = get_user_model()

class GardenAPITest(APITestCase):
    """Tests for the Garden API endpoints"""
    
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )
        
        # Create test plants
        self.plant1 = Plant.objects.create(
            common_name="Test Plant 1",
            scientific_name="Testus plantus",
            is_user_created=False,
            created_by=self.user
        )

        self.plant2 = Plant.objects.create(
            common_name="Test Plant 2",
            scientific_name="Testus secundus",
            is_user_created=False,
            created_by=self.user
        )
        
        # Create test gardens
        self.garden = Garden.objects.create(
            user=self.user,
            name="Test Garden",
            size_x=5,
            size_y=5
        )
        
        self.other_garden = Garden.objects.create(
            user=self.other_user,
            name="Other Garden",
            size_x=3,
            size_y=3
        )
        
        # Create garden logs
        self.garden_log = GardenLog.objects.create(
            garden=self.garden,
            plant=self.plant1,
            x_position=1,
            y_position=1,
            planted_date=timezone.now().date()
        )
        
        # Initialize the client and authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_gardens(self):
        """Test that users can list their own gardens"""
        url = reverse('gardens_api:garden-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Garden")
        
        # Check that other user's gardens are not included
        garden_ids = [garden['id'] for garden in response.data]
        self.assertNotIn(self.other_garden.id, garden_ids)

    def test_create_garden(self):
        """Test that users can create a garden"""
        url = reverse('gardens_api:garden-list')
        data = {
            'name': 'New Garden',
            'size_x': 4,
            'size_y': 4
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Garden')
        
        # Check garden was created in the database
        self.assertTrue(Garden.objects.filter(name='New Garden', user=self.user).exists())

    def test_update_garden(self):
        """Test that users can update their own garden"""
        url = reverse('gardens_api:garden-detail', args=[self.garden.id])
        data = {
            'name': 'Updated Garden Name',
            'size_x': 6,
            'size_y': 6
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Garden Name')
        
        # Check garden was updated in the database
        self.garden.refresh_from_db()
        self.assertEqual(self.garden.name, 'Updated Garden Name')
        self.assertEqual(self.garden.size_x, 6)
        self.assertEqual(self.garden.size_y, 6)

    def test_get_garden_grid(self):
        """Test getting the garden grid layout"""
        url = reverse('gardens_api:garden-grid', args=[self.garden.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.garden.name)
        self.assertEqual(len(response.data['cells']), self.garden.size_y)
        self.assertEqual(len(response.data['cells'][0]), self.garden.size_x)
        
        # Check the plant is in the right cell
        plant_cell = response.data['cells'][1][1]
        self.assertIsNotNone(plant_cell)
        self.assertEqual(plant_cell['common_name'], self.plant1.common_name)

    def test_garden_dashboard(self):
        """Test getting the garden dashboard data"""
        url = reverse('gardens_api:garden-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['garden_count'], 1)
        self.assertEqual(response.data['plant_count'], 1)
        
        # Check that garden data is included
        self.assertEqual(len(response.data['gardens']), 1)
        self.assertEqual(response.data['gardens'][0]['id'], self.garden.id)

    def test_update_grid(self):
        """Test updating the garden grid layout"""
        url = reverse('gardens_api:garden-update-grid', args=[self.garden.id])
        
        # Create a grid with a plant at position 2,2
        cells = [[None for _ in range(5)] for _ in range(5)]
        cells[2][2] = {'id': self.plant2.id}
        
        data = {'cells': cells}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the database was updated (old log deleted, new one created)
        self.assertEqual(GardenLog.objects.filter(garden=self.garden).count(), 1)
        log = GardenLog.objects.get(garden=self.garden)
        self.assertEqual(log.plant.id, self.plant2.id)
        self.assertEqual(log.x_position, 2)
        self.assertEqual(log.y_position, 2)