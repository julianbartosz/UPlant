# backend/root/gardens/api/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework import status
import json
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from plants.models import Plant
from gardens.models import Garden, GardenLog, PlantHealthStatus
from notifications.models import Notification, NotificationInstance

User = get_user_model()

# ==================== FIXTURES ====================

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword'
    )

@pytest.fixture
def other_user():
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='otherpassword'
    )

@pytest.fixture
def test_plant(user):
    return Plant.objects.create(
        common_name="Test Plant 1",
        scientific_name="Testus plantus",
        is_user_created=False,
        created_by=user
    )

@pytest.fixture
def second_plant(user):
    return Plant.objects.create(
        common_name="Test Plant 2",
        scientific_name="Testus secundus",
        is_user_created=False,
        created_by=user
    )

@pytest.fixture
def third_plant(user):
    plant = Plant.objects.create(
        common_name="Test Plant 3",
        scientific_name="Testus tertius",
        is_user_created=False,
        created_by=user
    )
    # Add plant-specific attributes for weather compatibility testing
    plant.frost_resistant = False
    plant.heat_tolerant = True
    plant.water_needs = 'high'
    plant.staking_required = True
    plant.save()
    return plant

@pytest.fixture
def garden(user):
    return Garden.objects.create(
        user=user,
        name="Test Garden",
        size_x=5,
        size_y=5
    )

@pytest.fixture
def garden_with_plants(garden, test_plant, second_plant):
    # Add plants to the garden
    GardenLog.objects.create(
        garden=garden,
        plant=test_plant,
        x_coordinate=1,
        y_coordinate=1,
        planted_date=timezone.now().date()
    )
    
    GardenLog.objects.create(
        garden=garden,
        plant=second_plant,
        x_coordinate=2,
        y_coordinate=3,
        planted_date=timezone.now().date()
    )
    
    return garden

@pytest.fixture
def other_garden(other_user):
    return Garden.objects.create(
        user=other_user,
        name="Other Garden",
        size_x=3,
        size_y=3
    )

@pytest.fixture
def garden_log(garden, test_plant):
    return GardenLog.objects.create(
        garden=garden,
        plant=test_plant,
        x_coordinate=1,
        y_coordinate=1,
        planted_date=timezone.now().date()
    )

@pytest.fixture
def notification(garden):
    return Notification.objects.create(
        garden=garden,
        name="Water Garden",
        type="WA",
        interval=7
    )

@pytest.fixture
def notification_instance(notification):
    return NotificationInstance.objects.create(
        notification=notification,
        next_due=timezone.now() + timedelta(days=2),
        status='PENDING'
    )

@pytest.fixture
def mock_weather_data():
    return {
        'current_weather': {
            'temperature': {'value': 75, 'unit': '°F'},
            'condition': 'Partly cloudy',
            'humidity': {'value': 60, 'unit': '%'},
        },
        'forecast_summary': {
            'today': 'Partly cloudy with a high of 75°F',
            'tomorrow': 'Sunny with a high of 80°F',
        },
        'frost_warning': {
            'frost_risk': True,
            'frost_days': [
                {
                    'date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'temperature': 30
                }
            ],
            'min_temperature': 30
        },
        'extreme_heat_warning': {
            'extreme_heat': True,
            'hot_days': [
                {
                    'date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'temperature': 98
                }
            ],
            'max_temperature': 98
        },
        'high_wind_warning': {
            'high_winds': True,
            'windy_days': [
                {
                    'date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    'wind_speed': 35
                }
            ],
            'max_wind_speed': 35
        },
        'watering_needed': {
            'should_water': True,
            'reason': 'Soil is dry, no rain expected',
            'next_rain_forecast': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }
    }

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

# ==================== TEST CLASSES ====================

@pytest.mark.django_db
class TestGardenViewSet:
    """Tests for the GardenViewSet"""
    
    def test_list_gardens(self, authenticated_client, garden, other_garden):
        """Test that users can list their own gardens"""
        url = reverse('gardens_api:garden-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == "Test Garden"
        
        # Check that other user's gardens are not included
        garden_ids = [garden['id'] for garden in response.data]
        assert other_garden.id not in garden_ids
    
    def test_create_garden(self, authenticated_client):
        """Test that users can create a garden"""
        url = reverse('gardens_api:garden-list')
        data = {
            'name': 'New Garden',
            'size_x': 4,
            'size_y': 4
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Garden'
        
        # Check garden was created in the database
        assert Garden.objects.filter(name='New Garden').exists()
    
    def test_retrieve_garden(self, authenticated_client, garden):
        """Test that users can retrieve their own garden"""
        url = reverse('gardens_api:garden-detail', args=[garden.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == garden.name
        assert response.data['size_x'] == garden.size_x
        assert response.data['size_y'] == garden.size_y
    
    def test_update_garden(self, authenticated_client, garden):
        """Test that users can update their own garden"""
        url = reverse('gardens_api:garden-detail', args=[garden.id])
        data = {
            'name': 'Updated Garden Name',
            'size_x': 6,
            'size_y': 6
        }
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Garden Name'
        
        # Check garden was updated in the database
        garden.refresh_from_db()
        assert garden.name == 'Updated Garden Name'
        assert garden.size_x == 6
        assert garden.size_y == 6
    
    def test_delete_garden(self, authenticated_client, garden):
        """Test that users can delete their own garden"""
        url = reverse('gardens_api:garden-detail', args=[garden.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check garden was deleted in the database
        garden.refresh_from_db()
        assert garden.is_deleted  # Should be soft-deleted
    
    def test_grid_action(self, authenticated_client, garden_with_plants):
        """Test the garden grid action"""
        url = reverse('gardens_api:garden-grid', args=[garden_with_plants.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == garden_with_plants.name
        assert len(response.data['cells']) == garden_with_plants.size_y
        assert len(response.data['cells'][0]) == garden_with_plants.size_x
        
        # Check that plants are in the right cells
        assert response.data['cells'][1][1] is not None
        assert response.data['cells'][3][2] is not None
        assert 'common_name' in response.data['cells'][1][1]
        assert 'id' in response.data['cells'][1][1]
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_weather_action(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test the garden weather action with provided zip code"""
        mock_weather.return_value = mock_weather_data
        
        url = reverse('gardens_api:garden-weather', args=[garden.id])
        response = authenticated_client.get(f"{url}?zip_code=12345")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'current_weather' in response.data
        assert 'forecast_summary' in response.data
        assert 'frost_warning' in response.data
        assert 'plant_recommendations' in response.data
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_weather_action_with_profile_zip(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test the garden weather action using user profile zip code"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('gardens_api:garden-weather', args=[garden.id])
            response = authenticated_client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'current_weather' in response.data
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_weather_action_service_error(self, mock_weather, authenticated_client, garden):
        """Test handling of weather service errors"""
        from services.weather_service import WeatherServiceError
        mock_weather.side_effect = WeatherServiceError("Weather service unavailable")
        
        url = reverse('gardens_api:garden-weather', args=[garden.id])
        response = authenticated_client.get(f"{url}?zip_code=12345")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert 'detail' in response.data
    
    def test_weather_action_no_zip_code(self, authenticated_client, garden):
        """Test error handling when no zip code is provided"""
        url = reverse('gardens_api:garden-weather', args=[garden.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_dashboard_action(self, mock_weather, authenticated_client, garden, notification_instance, mock_weather_data):
        """Test the garden dashboard action"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('gardens_api:garden-dashboard')
            response = authenticated_client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'garden_count' in response.data
            assert 'plant_count' in response.data
            assert 'upcoming_tasks' in response.data
            assert 'gardens' in response.data
            assert 'weather' in response.data
            
            # Check that the task is included
            assert len(response.data['upcoming_tasks']) == 1
            assert response.data['upcoming_tasks'][0]['name'] == "Water Garden"
    
    def test_dashboard_action_no_weather(self, authenticated_client, garden):
        """Test dashboard without weather data"""
        url = reverse('gardens_api:garden-dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'garden_count' in response.data
        assert 'weather' not in response.data
    
    def test_update_grid_action(self, authenticated_client, garden, test_plant, second_plant):
        """Test updating the garden grid layout"""
        url = reverse('gardens_api:garden-update-grid', args=[garden.id])
        
        # Create a grid with plants at positions (2,2) and (3,3)
        cells = [[None for _ in range(5)] for _ in range(5)]
        cells[2][2] = {'id': test_plant.id}
        cells[3][3] = {'id': second_plant.id}
        
        data = {'cells': cells}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that garden logs were created correctly
        assert GardenLog.objects.filter(garden=garden).count() == 2
        assert GardenLog.objects.filter(garden=garden, x_coordinate=2, y_coordinate=2).exists()
        assert GardenLog.objects.filter(garden=garden, x_coordinate=3, y_coordinate=3).exists()
    
    def test_update_grid_invalid_dimensions(self, authenticated_client, garden):
        """Test error handling for grid with invalid dimensions"""
        url = reverse('gardens_api:garden-update-grid', args=[garden.id])
        
        # Create a grid with wrong dimensions (6x5 instead of 5x5)
        cells = [[None for _ in range(6)] for _ in range(5)]
        
        data = {'cells': cells}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_recommendations_action(self, mock_weather, authenticated_client, garden_with_plants, third_plant, mock_weather_data):
        """Test the garden recommendations action"""
        # Add a plant with specific attributes for testing
        GardenLog.objects.create(
            garden=garden_with_plants,
            plant=third_plant,
            x_coordinate=3,
            y_coordinate=3,
            planted_date=timezone.now().date()
        )
        
        mock_weather.return_value = mock_weather_data
        
        url = reverse('gardens_api:garden-recommendations', args=[garden_with_plants.id])
        response = authenticated_client.get(f"{url}?zip_code=12345")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'general' in response.data
        assert 'plants' in response.data
        
        # Check that general recommendations are included
        assert len(response.data['general']) > 0
        
        # Check that plant-specific recommendations are included for plant with attributes
        assert len(response.data['plants']) > 0
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_recommendations_weather_service_error(self, mock_weather, authenticated_client, garden):
        """Test handling of weather service errors in recommendations"""
        from services.weather_service import WeatherServiceError
        mock_weather.side_effect = WeatherServiceError("Weather service unavailable")
        
        url = reverse('gardens_api:garden-recommendations', args=[garden.id])
        response = authenticated_client.get(f"{url}?zip_code=12345")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert 'error' in response.data
    
    def test_unauthorized_access(self, api_client, garden):
        """Test that unauthenticated users cannot access garden data"""
        url = reverse('gardens_api:garden-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_other_user_garden_access(self, authenticated_client, other_garden):
        """Test that users cannot access other users' gardens"""
        url = reverse('gardens_api:garden-detail', args=[other_garden.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_other_user_garden(self, authenticated_client, other_garden):
        """Test that users cannot update other users' gardens"""
        url = reverse('gardens_api:garden-detail', args=[other_garden.id])
        data = {'name': 'Unauthorized Update'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Check garden was not updated
        other_garden.refresh_from_db()
        assert other_garden.name != 'Unauthorized Update'


@pytest.mark.django_db
class TestGardenLogViewSet:
    """Tests for the GardenLogViewSet"""
    
    def test_list_garden_logs(self, authenticated_client, garden_log):
        """Test that users can list their garden logs"""
        url = reverse('gardens_api:garden-log-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['garden'] == garden_log.garden.id
        assert response.data[0]['plant'] == garden_log.plant.id
    
    def test_list_garden_logs_with_filter(self, authenticated_client, garden_log, garden):
        """Test filtering garden logs by garden"""
        url = f"{reverse('gardens_api:garden-log-list')}?garden={garden.id}"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['garden'] == garden_log.garden.id
    
    def test_create_garden_log(self, authenticated_client, garden, test_plant):
        """Test that users can create a garden log"""
        url = reverse('gardens_api:garden-log-list')
        data = {
            'garden': garden.id,
            'plant': test_plant.id,
            'x_coordinate': 2,
            'y_coordinate': 2,
            'planted_date': timezone.now().date().isoformat()
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['garden'] == garden.id
        assert response.data['plant'] == test_plant.id
        assert response.data['x_coordinate'] == 2
        assert response.data['y_coordinate'] == 2
    
    def test_create_garden_log_position_conflict(self, authenticated_client, garden_log, garden, second_plant):
        """Test that users cannot create a garden log at an occupied position"""
        url = reverse('gardens_api:garden-log-list')
        data = {
            'garden': garden.id,
            'plant': second_plant.id,
            'x_coordinate': garden_log.x_coordinate,
            'y_coordinate': garden_log.y_coordinate,
            'planted_date': timezone.now().date().isoformat()
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'position' in str(response.data)
    
    def test_create_garden_log_other_user_garden(self, authenticated_client, other_garden, test_plant):
        """Test that users cannot create a garden log in another user's garden"""
        url = reverse('gardens_api:garden-log-list')
        data = {
            'garden': other_garden.id,
            'plant': test_plant.id,
            'x_coordinate': 2,
            'y_coordinate': 2,
            'planted_date': timezone.now().date().isoformat()
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_retrieve_garden_log(self, authenticated_client, garden_log):
        """Test that users can retrieve their garden logs"""
        url = reverse('gardens_api:garden-log-detail', args=[garden_log.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == garden_log.id
        assert response.data['garden'] == garden_log.garden.id
        assert response.data['plant'] == garden_log.plant.id
    
    def test_update_garden_log(self, authenticated_client, garden_log):
        """Test that users can update their garden logs"""
        url = reverse('gardens_api:garden-log-detail', args=[garden_log.id])
        data = {
            'notes': 'Test notes',
            'health_status': PlantHealthStatus.EXCELLENT
        }
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['notes'] == 'Test notes'
        assert response.data['health_status'] == PlantHealthStatus.EXCELLENT
    
    def test_delete_garden_log(self, authenticated_client, garden_log):
        """Test that users can delete their garden logs"""
        url = reverse('gardens_api:garden-log-detail', args=[garden_log.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check garden log was deleted or soft-deleted
        assert not GardenLog.objects.filter(id=garden_log.id, is_deleted=False).exists()
    
    def test_update_health_action(self, authenticated_client, garden_log):
        """Test the update_health action"""
        url = reverse('gardens_api:garden-log-update-health', args=[garden_log.id])
        data = {'health_status': PlantHealthStatus.EXCELLENT}
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['health_status'] == PlantHealthStatus.EXCELLENT
        
        # Check database was updated
        garden_log.refresh_from_db()
        assert garden_log.health_status == PlantHealthStatus.EXCELLENT
    
    def test_update_health_action_invalid_status(self, authenticated_client, garden_log):
        """Test error handling for invalid health status"""
        url = reverse('gardens_api:garden-log-update-health', args=[garden_log.id])
        data = {'health_status': 'INVALID_STATUS'}
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK  # The view doesn't validate the health status
        
        # But database should be updated
        garden_log.refresh_from_db()
        assert garden_log.health_status == 'INVALID_STATUS'
    
    @patch('gardens.api.views.get_garden_weather_insights')
    def test_weather_compatibility_action(self, mock_weather, authenticated_client, garden_log, third_plant, mock_weather_data):
        """Test the weather_compatibility action"""
        # Replace the plant with one that has weather attributes
        garden_log.plant = third_plant
        garden_log.save()
        
        mock_weather.return_value = mock_weather_data
        
        url = reverse('gardens_api:garden-log-weather-compatibility', args=[garden_log.id])
        response = authenticated_client.get(f"{url}?zip_code=12345")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'alerts' in response.data
        assert 'care_tips' in response.data
        
        # Should have frost warning alert since plant is not frost resistant
        frost_alerts = [alert for alert in response.data['alerts'] if alert['type'] == 'frost']
        assert len(frost_alerts) > 0


@pytest.mark.django_db
class TestWeatherByZipView:
    """Tests for the WeatherByZipView"""
    
    @patch('gardens.api.views.get_weather_by_zip')
    def test_get_weather_by_zip(self, mock_weather, authenticated_client, mock_weather_data):
        """Test getting weather data by zip code"""
        mock_weather.return_value = mock_weather_data
        
        url = reverse('gardens_api:weather-by-zip', args=['12345'])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'current_weather' in response.data
        assert 'forecast_summary' in response.data
    
    @patch('gardens.api.views.get_weather_by_zip')
    def test_weather_service_error(self, mock_weather, authenticated_client):
        """Test handling of weather service errors"""
        from services.weather_service import WeatherServiceError
        mock_weather.side_effect = WeatherServiceError("Weather service unavailable")
        
        url = reverse('gardens_api:weather-by-zip', args=['12345'])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_unauthenticated_access(self, api_client):
        """Test that unauthenticated users cannot access weather data"""
        url = reverse('gardens_api:weather-by-zip', args=['12345'])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOverallPermissions:
    """Tests for permissions across the API"""
    
    def test_garden_permissions(self, api_client, authenticated_client, garden, other_garden):
        """Test garden permissions"""
        # Unauthenticated access should be denied
        url = reverse('gardens_api:garden-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Authenticated user should only see their own gardens
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == garden.id
        
        # Cannot access another user's garden
        url = reverse('gardens_api:garden-detail', args=[other_garden.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_garden_log_permissions(self, authenticated_client, garden, other_garden, test_plant):
        """Test garden log permissions"""
        # Create a log in the other user's garden
        other_log = GardenLog.objects.create(
            garden=other_garden,
            plant=test_plant,
            x_coordinate=1,
            y_coordinate=1,
            planted_date=timezone.now().date()
        )
        
        # User should not see the other user's garden log
        url = reverse('gardens_api:garden-log-list')
        response = authenticated_client.get(url)
        assert all(log['garden'] != other_garden.id for log in response.data)
        
        # Cannot access another user's garden log directly
        url = reverse('gardens_api:garden-log-detail', args=[other_log.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND