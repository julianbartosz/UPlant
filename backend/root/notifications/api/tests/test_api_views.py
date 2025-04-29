# backend/root/notifications/api/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import json
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from plants.models import Plant
from gardens.models import Garden
from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation, NotifTypes
from services.weather_service import WeatherServiceError

User = get_user_model()

# ==================== FIXTURES ====================

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword'
    )

@pytest.fixture
def garden(user):
    return Garden.objects.create(
        user=user,
        name="Test Garden",
        size_x=5,
        size_y=5
    )

@pytest.fixture
def test_plant(db):
    return Plant.objects.create(
        common_name="Test Plant",
        scientific_name="Testus plantus",
        is_user_created=False,
        slug="testus-plantus"
    )

@pytest.fixture
def second_plant(db):
    return Plant.objects.create(
        common_name="Second Plant",
        scientific_name="Testus secundus",
        is_user_created=False,
        slug="testus-secundus"
    )

@pytest.fixture
def water_notification(garden, test_plant):
    notification = Notification.objects.create(
        garden=garden,
        name="Water Notification",
        type=NotifTypes.WA,
        interval=7
    )
    NotificationPlantAssociation.objects.create(
        notification=notification,
        plant=test_plant
    )
    return notification

@pytest.fixture
def fertilize_notification(garden):
    return Notification.objects.create(
        garden=garden,
        name="Fertilize Notification",
        type=NotifTypes.FE,
        interval=14
    )

@pytest.fixture
def pending_instance(water_notification):
    return NotificationInstance.objects.create(
        notification=water_notification,
        next_due=timezone.now() + timedelta(days=2),
        status='PENDING'
    )

@pytest.fixture
def overdue_instance(water_notification):
    return NotificationInstance.objects.create(
        notification=water_notification,
        next_due=timezone.now() - timedelta(days=2),
        status='PENDING'
    )

@pytest.fixture
def completed_instance(fertilize_notification):
    return NotificationInstance.objects.create(
        notification=fertilize_notification,
        next_due=timezone.now() - timedelta(days=1),
        status='COMPLETED',
        completed_at=timezone.now() - timedelta(hours=12)
    )

@pytest.fixture
def mock_weather_data():
    return {
        'current_weather': {
            'temperature': {'value': 75, 'unit': '°F'},
            'condition': 'Partly cloudy',
            'humidity': {'value': 60, 'unit': '%'},
        },
        'frost_warning': {
            'frost_risk': True,
            'frost_days': [
                {
                    'date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'temperature': 30
                }
            ]
        },
        'extreme_heat_warning': {
            'extreme_heat': True,
            'hot_days': [
                {
                    'date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'temperature': 98
                }
            ]
        },
        'high_wind_warning': {
            'high_winds': True,
            'windy_days': [
                {
                    'date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    'wind_speed': 35
                }
            ]
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
class TestNotificationViewSet:
    """Tests for the NotificationViewSet"""
    
    def test_list_notifications(self, authenticated_client, water_notification):
        """Test listing notifications"""
        url = reverse('notifications_api:notification-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == "Water Notification"
    
    def test_create_notification(self, authenticated_client, garden):
        """Test creating a new notification"""
        url = reverse('notifications_api:notification-list')
        data = {
            'garden': garden.id,
            'name': "New Notification",
            'type': NotifTypes.PR,
            'interval': 14
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Notification"
        assert response.data['type'] == NotifTypes.PR
    
    def test_retrieve_notification(self, authenticated_client, water_notification):
        """Test retrieving a single notification"""
        url = reverse('notifications_api:notification-detail', kwargs={'pk': water_notification.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == water_notification.id
        assert response.data['name'] == water_notification.name
    
    def test_update_notification(self, authenticated_client, water_notification):
        """Test updating a notification"""
        url = reverse('notifications_api:notification-detail', kwargs={'pk': water_notification.id})
        data = {
            'name': "Updated Notification",
            'interval': 10
        }
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Updated Notification"
        assert response.data['interval'] == 10
    
    def test_delete_notification(self, authenticated_client, water_notification):
        """Test deleting a notification"""
        url = reverse('notifications_api:notification-detail', kwargs={'pk': water_notification.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(id=water_notification.id).exists()
    
    def test_add_plant(self, authenticated_client, water_notification, second_plant):
        """Test adding a plant to a notification"""
        url = reverse('notifications_api:notification-add-plant', kwargs={'pk': water_notification.id})
        data = {'plant_id': second_plant.id}
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert water_notification.plants.filter(id=second_plant.id).exists()
    
    def test_add_plant_with_custom_interval(self, authenticated_client, water_notification, second_plant):
        """Test adding a plant with custom interval to a notification"""
        url = reverse('notifications_api:notification-add-plant', kwargs={'pk': water_notification.id})
        data = {
            'plant_id': second_plant.id,
            'custom_interval': 14
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Check if custom interval was saved
        association = NotificationPlantAssociation.objects.get(
            notification=water_notification, 
            plant=second_plant
        )
        assert association.custom_interval == 14
    
    def test_remove_plant(self, authenticated_client, water_notification, test_plant):
        """Test removing a plant from a notification"""
        url = reverse('notifications_api:notification-remove-plant', kwargs={'pk': water_notification.id})
        data = {'plant_id': test_plant.id}
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['deleted'] is True
        assert not water_notification.plants.filter(id=test_plant.id).exists()
    
    def test_dashboard(self, authenticated_client, pending_instance, overdue_instance):
        """Test the dashboard endpoint"""
        url = reverse('notifications_api:notification-dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'overdue' in response.data
        assert 'today' in response.data
        assert 'tomorrow' in response.data
        assert 'this_week' in response.data
        assert 'later' in response.data
        
        # Check if our overdue instance is in the overdue list
        assert len(response.data['overdue']) == 1
    
    def test_by_garden(self, authenticated_client, water_notification, fertilize_notification):
        """Test the by_garden endpoint"""
        url = reverse('notifications_api:notification-by-garden')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # One garden
        assert response.data[0]['garden_id'] == water_notification.garden.id
    
    def test_weather_endpoint_no_weather_service(self, authenticated_client, garden):
        """Test the weather endpoint with no weather service available"""
        url = reverse('notifications_api:notification-weather')
        response = authenticated_client.get(url)
        
        # Should still return 200 with a message
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
    
    @patch('notifications.api.views.get_garden_weather_insights')
    def test_weather_endpoint_with_weather_data(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test the weather endpoint with mock weather data"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('notifications_api:notification-weather')
            response = authenticated_client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert isinstance(response.data, list)
            assert len(response.data) > 0
            assert 'alerts' in response.data[0]
            
            # Check if we have the expected alert types
            alert_types = [alert['type'] for alert in response.data[0]['alerts']]
            assert 'FROST' in alert_types
            assert 'HEAT' in alert_types
            assert 'WIND' in alert_types
            assert 'WATER' in alert_types
    
    @patch('notifications.api.views.get_garden_weather_insights')
    def test_create_weather_notification_frost(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test creating a weather notification for frost"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('notifications_api:notification-create-weather-notifications')
            data = {
                'garden_id': garden.id,
                'alert_type': 'FROST'
            }
            
            response = authenticated_client.post(url, data)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
            
            # Verify a notification was created
            notification = Notification.objects.filter(
                garden=garden, 
                type='WE',
                subtype='FROST'
            ).first()
            
            assert notification is not None
            assert 'Frost Warning' in notification.name
            
            # Check if an instance was created
            assert notification.instances.filter(status='PENDING').exists()
    
    @patch('notifications.api.views.get_garden_weather_insights')
    def test_create_weather_notification_heat(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test creating a weather notification for heat"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('notifications_api:notification-create-weather-notifications')
            data = {
                'garden_id': garden.id,
                'alert_type': 'HEAT'
            }
            
            response = authenticated_client.post(url, data)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
            
            # Verify a notification was created
            notification = Notification.objects.filter(
                garden=garden, 
                type='WE',
                subtype='HEAT'
            ).first()
            
            assert notification is not None
            assert 'Heat Warning' in notification.name
    
    @patch('notifications.api.views.get_garden_weather_insights')
    def test_create_weather_notification_wind(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test creating a weather notification for wind"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('notifications_api:notification-create-weather-notifications')
            data = {
                'garden_id': garden.id,
                'alert_type': 'WIND'
            }
            
            response = authenticated_client.post(url, data)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
            
            # Verify a notification was created
            notification = Notification.objects.filter(
                garden=garden, 
                type='WE',
                subtype='WIND'
            ).first()
            
            assert notification is not None
            assert 'Wind Warning' in notification.name
    
    @patch('notifications.api.views.get_garden_weather_insights')
    def test_create_weather_notification_water(self, mock_weather, authenticated_client, garden, mock_weather_data):
        """Test creating a weather notification for watering"""
        mock_weather.return_value = mock_weather_data
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('notifications_api:notification-create-weather-notifications')
            data = {
                'garden_id': garden.id,
                'alert_type': 'WATER'
            }
            
            response = authenticated_client.post(url, data)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
            
            # Verify a notification was created
            notification = Notification.objects.filter(
                garden=garden, 
                type='WA',
                subtype='WEATHER'
            ).first()
            
            assert notification is not None
            assert 'Watering needed' in notification.name
    
    @patch('notifications.api.views.get_garden_weather_insights')
    def test_weather_service_error(self, mock_weather, authenticated_client, garden):
        """Test handling of weather service errors"""
        mock_weather.side_effect = WeatherServiceError("Service unavailable")
        
        # Mock user profile with zip_code
        with patch.object(authenticated_client.handler._force_user, 'profile', 
                         create=True) as mock_profile:
            mock_profile.zip_code = '12345'
            
            url = reverse('notifications_api:notification-create-weather-notifications')
            data = {
                'garden_id': garden.id,
                'alert_type': 'FROST'
            }
            
            response = authenticated_client.post(url, data)
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert 'error' in response.data
    
    def test_create_notification_for_other_user_garden(self, authenticated_client, db):
        """Test that a user cannot create notifications for another user's garden"""
        # Create another user and their garden
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        
        other_garden = Garden.objects.create(
            user=other_user,
            name="Other Garden",
            size_x=10,
            size_y=10
        )
        
        url = reverse('notifications_api:notification-list')
        data = {
            'garden': other_garden.id,
            'name': "Invalid Notification",
            'type': NotifTypes.WA,
            'interval': 7
        }
        
        response = authenticated_client.post(url, data)
        
        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestNotificationInstanceViewSet:
    """Tests for the NotificationInstanceViewSet"""
    
    def test_list_notification_instances(self, authenticated_client, pending_instance, overdue_instance):
        """Test listing notification instances"""
        url = reverse('notifications_api:notification-instance-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_retrieve_notification_instance(self, authenticated_client, pending_instance):
        """Test retrieving a single notification instance"""
        url = reverse('notifications_api:notification-instance-detail', kwargs={'pk': pending_instance.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == pending_instance.id
        assert response.data['status'] == 'PENDING'
    
    def test_create_notification_instance(self, authenticated_client, water_notification):
        """Test creating a notification instance"""
        url = reverse('notifications_api:notification-instance-list')
        data = {
            'notification': water_notification.id,
            'next_due': (timezone.now() + timedelta(days=5)).isoformat(),
            'status': 'PENDING'
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['notification'] == water_notification.id
        assert response.data['status'] == 'PENDING'
    
    def test_complete_notification_instance(self, authenticated_client, pending_instance):
        """Test completing a notification instance"""
        url = reverse('notifications_api:notification-instance-complete', kwargs={'pk': pending_instance.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verify the instance status changed
        pending_instance.refresh_from_db()
        assert pending_instance.status == 'COMPLETED'
        assert pending_instance.completed_at is not None
    
    def test_skip_notification_instance(self, authenticated_client, pending_instance):
        """Test skipping a notification instance"""
        url = reverse('notifications_api:notification-instance-skip', kwargs={'pk': pending_instance.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verify the instance status changed
        pending_instance.refresh_from_db()
        assert pending_instance.status == 'SKIPPED'
    
    def test_bulk_complete_notification_instances(self, authenticated_client, pending_instance, overdue_instance):
        """Test bulk-completing notification instances"""
        url = reverse('notifications_api:notification-instance-bulk-complete')
        data = {
            'instance_ids': [pending_instance.id, overdue_instance.id]
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['completed'] == 2
        
        # Verify the instances are completed
        pending_instance.refresh_from_db()
        overdue_instance.refresh_from_db()
        assert pending_instance.status == 'COMPLETED'
        assert overdue_instance.status == 'COMPLETED'
    
    def test_upcoming_notification_instances(self, authenticated_client, pending_instance, overdue_instance):
        """Test getting upcoming notification instances"""
        url = reverse('notifications_api:notification-instance-upcoming')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Test with custom days parameter
        url = f"{url}?days=1"
        response = authenticated_client.get(url)
        
        # Only overdue instance should be included (< 1 day from now)
        assert len(response.data) == 1
        assert response.data[0]['id'] == overdue_instance.id
    
    def test_unauthorized_access(self, api_client, pending_instance):
        """Test unauthorized access to notification instances"""
        # Try accessing without authentication
        url = reverse('notifications_api:notification-instance-list')
        response = api_client.get(url)
        
        # Should require authentication
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_complete_other_user_notification(self, authenticated_client, db):
        """Test that a user cannot complete another user's notification"""
        # Create another user with their garden and notification
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        
        other_garden = Garden.objects.create(
            user=other_user,
            name="Other Garden",
            size_x=10,
            size_y=10
        )
        
        other_notification = Notification.objects.create(
            garden=other_garden,
            name="Other Notification",
            type=NotifTypes.WA,
            interval=7
        )
        
        other_instance = NotificationInstance.objects.create(
            notification=other_notification,
            next_due=timezone.now(),
            status='PENDING'
        )
        
        # Try to complete it
        url = reverse('notifications_api:notification-instance-complete', kwargs={'pk': other_instance.id})
        response = authenticated_client.post(url)
        
        # Should be forbidden (404 as it's filtered by queryset)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPermissions:
    """Tests for permissions and authentication"""
    
    def test_unauthenticated_access(self, api_client, water_notification):
        """Test that unauthenticated access is denied"""
        urls = [
            reverse('notifications_api:notification-list'),
            reverse('notifications_api:notification-detail', kwargs={'pk': water_notification.id}),
            reverse('notifications_api:notification-dashboard'),
            reverse('notifications_api:notification-by-garden'),
            reverse('notifications_api:notification-weather'),
        ]
        
        for url in urls:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_other_user_notification_access(self, authenticated_client, db):
        """Test that a user cannot access another user's notifications"""
        # Create another user with their garden and notification
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        
        other_garden = Garden.objects.create(
            user=other_user,
            name="Other Garden",
            size_x=10,
            size_y=10
        )
        
        other_notification = Notification.objects.create(
            garden=other_garden,
            name="Other Notification",
            type=NotifTypes.WA,
            interval=7
        )
        
        # Try to access the other notification
        url = reverse('notifications_api:notification-detail', kwargs={'pk': other_notification.id})
        response = authenticated_client.get(url)
        
        # Should return 404 (not found) because queryset is filtered by user
        assert response.status_code == status.HTTP_404_NOT_FOUND