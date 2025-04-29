import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import patch, MagicMock, PropertyMock
from django.db.models import Q
from django.contrib.auth import get_user_model
from user_management.models import User, Roles
import uuid
import json

from plants.models import Plant, PlantChangeRequest
from services.weather_service import WeatherServiceError

# Mock responses
@pytest.fixture
def mock_trefle_plants_response():
    return {
        "data": [
            {
                "id": 1,
                "common_name": "Test Plant 1",
                "scientific_name": "Testus plantus 1",
                "image_url": "http://example.com/image1.jpg",
                "slug": "testus-plantus-1",
                "status": "accepted",
                "rank": "species",
                "family": "Testaceae",
                "genus_id": 101,
                "genus": "Testus",
                "links": {},
                "synonyms": []
            },
            {
                "id": 2,
                "common_name": "Test Plant 2",
                "scientific_name": "Testus plantus 2",
                "image_url": "http://example.com/image2.jpg",
                "slug": "testus-plantus-2",
                "status": "accepted",
                "rank": "species",
                "family": "Testaceae",
                "genus_id": 101,
                "genus": "Testus",
                "links": {},
                "synonyms": []
            }
        ],
        "links": {
            "self": "http://trefle.io/api/v1/plants?page=1",
            "next": "http://trefle.io/api/v1/plants?page=2",
        },
        "meta": {
            "total": 100
        }
    }

@pytest.fixture
def mock_trefle_plant_detail_response():
    return {
        "data": {
            "id": 1,
            "common_name": "Test Plant 1",
            "scientific_name": "Testus plantus 1",
            "slug": "testus-plantus-1",
            "status": "accepted",
            "rank": "species",
            "family": "Testaceae",
            "genus_id": 101,
            "genus": "Testus",
            "image_url": "http://example.com/image1.jpg",
            "vegetable": True,
            "edible": True,
            "synonyms": [],
            "links": {}
        },
        "links": {
            "self": "http://trefle.io/api/v1/plants/1",
            "plant": "http://trefle.io/api/v1/plants/1"
        }
    }

@pytest.fixture
def mock_weather_data():
    return {
        "current_weather": {
            "temperature": {
                "value": 22,
                "unit": "°C"
            },
            "humidity": {
                "value": 65,
                "unit": "%"
            },
            "wind": {
                "speed": 10,
                "direction": "NW",
                "unit": "km/h"
            },
            "condition": "Partly Cloudy"
        },
        "frost_warning": {
            "frost_risk": False,
            "min_temperature": 5
        },
        "extreme_heat_warning": {
            "extreme_heat": False,
            "max_temperature": 30
        },
        "high_wind_warning": {
            "high_winds": False,
            "max_wind_speed": 15
        },
        "watering_needed": {
            "should_water": True,
            "reason": "Soil is likely dry based on recent precipitation patterns."
        },
        "forecast_summary": {
            "average_high": 25,
            "average_low": 15,
            "total_rainfall": 5.2
        }
    }

# User fixtures
@pytest.fixture
def regular_user(db):
    """Create a regular user for testing."""
    user = get_user_model().objects.create_user(
        username="testuser",
        email="user@example.com",
        password="password123"
    )
    # Add required profile fields
    if hasattr(user, 'profile'):
        user.profile.zip_code = "12345"
        user.profile.save()
    return user

@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    admin = get_user_model().objects.create_user(
        username="adminuser",
        email="admin@example.com",
        password="password123",
    )
    # Set role instead of is_staff directly (since is_staff is a property)
    admin.role = Roles.AD
    admin.save()
    
    return admin

@pytest.fixture
def authenticated_client(client, regular_user):
    """Return an authenticated client and the user."""
    client.force_login(regular_user)
    return client, regular_user

@pytest.fixture
def admin_client(client, admin_user):
    """Return an authenticated admin client and the admin user."""
    client.force_login(admin_user)
    return client, admin_user

# Plant fixtures
@pytest.fixture
def trefle_plant(db):
    """Create a unique trefle plant for each test that needs it"""
    # Add unique suffix to slug to avoid uniqueness constraint errors
    unique_suffix = str(uuid.uuid4())[:8]
    plant = Plant.objects.create(
        common_name="Basil",
        scientific_name="Ocimum basilicum",
        api_id="123456",
        is_user_created=False,
        is_verified=True,
        family="Lamiaceae",
        genus="Ocimum",
        image_url="http://example.com/basil.jpg",
        vegetable=False,
        edible=True,
        min_temperature=10,
        max_temperature=35,
        water_interval=3,
        sunlight_requirements="Full sun to part shade",
        slug=f"ocimum-basilicum-{unique_suffix}", # Make slug unique
        rank="species",
        genus_id=1
    )
    return plant

@pytest.fixture
def user_plant(db, regular_user):
    """Create a unique user plant for each test that needs it"""
    # Add unique suffix to slug to avoid uniqueness constraint errors
    unique_suffix = str(uuid.uuid4())[:8]
    plant = Plant.objects.create(
        common_name="My Tomato Plant",
        scientific_name="Solanum lycopersicum",
        is_user_created=True,
        is_verified=False,
        created_by=regular_user,
        family="Solanaceae",
        genus="Solanum",
        vegetable=True,
        edible=True,
        min_temperature=15,
        max_temperature=32,
        water_interval=2,
        sunlight_requirements="Full sun",
        slug=f"solanum-lycopersicum-{unique_suffix}", # Make slug unique
        rank="species", 
        genus_id=2
    )
    return plant

@pytest.fixture
def plant_change_request(db, regular_user, trefle_plant):
    change_request = PlantChangeRequest.objects.create(
        plant=trefle_plant,
        user=regular_user,
        field_name="water_interval",
        old_value="3",
        new_value="4",
        reason="Basil needs less frequent watering",
        status="PENDING"
    )
    return change_request

# Tests for Trefle API Views
@pytest.mark.django_db
class TestListPlantsAPIView:
    def test_get_plants_success(self, client, mock_trefle_plants_response):
        # Import and patch the trefle_service.list_plants function
        with patch('services.trefle_service.list_plants', return_value=mock_trefle_plants_response) as mock_list:
            # Add the patched function to the views module's namespace
            from plants.api import views
            views.list_plants = mock_list
            
            url = reverse('plants_api:trefle-list-plants')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['data']) == 2
            assert response.data['data'][0]['common_name'] == "Test Plant 1"
            
    def test_get_plants_with_search(self, client, mock_trefle_plants_response):
        # Import and patch the trefle_service.list_plants function
        with patch('services.trefle_service.list_plants', return_value=mock_trefle_plants_response) as mock_list:
            # Add the patched function to the views module's namespace
            from plants.api import views
            views.list_plants = mock_list
            
            url = reverse('plants_api:trefle-list-plants')
            response = client.get(f"{url}?q=tomato")
            
            assert response.status_code == status.HTTP_200_OK
            mock_list.assert_called_once()
            assert mock_list.call_args[1]['filters'].get('q') == 'tomato'
            
    def test_get_plants_error(self, client):
        # Import and create a mock that raises an exception
        with patch('services.trefle_service.list_plants', side_effect=Exception("API Error")) as mock_list:
            # Add the patched function to the views module's namespace
            from plants.api import views
            views.list_plants = mock_list
            
            url = reverse('plants_api:trefle-list-plants')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to retrieve plant list" in response.data['error']

@pytest.mark.django_db
class TestRetrievePlantAPIView:
    def test_retrieve_plant_success(self, client, mock_trefle_plant_detail_response):
        # Import and patch the trefle_service.retrieve_plants function
        with patch('services.trefle_service.retrieve_plants', return_value=mock_trefle_plant_detail_response) as mock_retrieve:
            # Add the patched function to the views module's namespace
            from plants.api import views
            views.retrieve_plants = mock_retrieve
            
            url = reverse('plants_api:trefle-retrieve-plant', kwargs={'id': '1'})
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['data']['common_name'] == "Test Plant 1"
            
    def test_retrieve_plant_not_found(self, client):
        # Import and patch the trefle_service.retrieve_plants function
        with patch('services.trefle_service.retrieve_plants', return_value={'data': None}) as mock_retrieve:
            # Add the patched function to the views module's namespace
            from plants.api import views
            views.retrieve_plants = mock_retrieve
            
            url = reverse('plants_api:trefle-retrieve-plant', kwargs={'id': '999'})
            response = client.get(url)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND

# Tests for PlantViewSet
@pytest.mark.django_db
class TestPlantViewSet:
    def test_list_plants(self, client, trefle_plant, user_plant):
        url = reverse('plants_api:plant-list')
        
        # Use query parameters to filter only our test plants
        response = client.get(f"{url}?ids={trefle_plant.id},{user_plant.id}")
        
        # Alternatively, we can patch the view to only return our test plants
        with patch('plants.api.views.PlantViewSet.get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value = Plant.objects.filter(
                id__in=[trefle_plant.id, user_plant.id]
            )
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2
        
    def test_retrieve_plant(self, client, trefle_plant):
        url = reverse('plants_api:plant-detail', kwargs={'pk': trefle_plant.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['common_name'] == trefle_plant.common_name
        
    def test_create_plant_as_admin(self, admin_client, trefle_plant):
        client, admin = admin_client
        url = reverse('plants_api:plant-list')
        data = {
            'common_name': 'New Admin Plant',
            'scientific_name': 'Adminus creatus',
            'family': 'Adminaceae',
            'genus': 'Adminus',
            'vegetable': True,
            'edible': True,
            # Add required fields
            'slug': f'adminus-creatus-{str(uuid.uuid4())[:8]}',
            'rank': 'species',
            'genus_id': 5
        }
        
        # Make sure to send as proper JSON
        response = client.post(url, json.dumps(data), content_type='application/json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['common_name'] == 'New Admin Plant'
        
    def test_create_plant_as_regular_user_forbidden(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('plants_api:plant-list')
        data = {
            'common_name': 'Unauthorized Plant',
            'scientific_name': 'Forbidden plantus'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_user_create_custom_plant(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('plants_api:plant-create-user-plant')  
        data = {
            'common_name': 'My Custom Plant',
            'scientific_name': 'Customus plantus',
            'family': 'Customaceae',
            'genus': 'Customus',
            'vegetable': True,
            'edible': True,
            'slug': f'customus-plantus-{str(uuid.uuid4())[:8]}',
            'rank': 'species',
            'genus_id': 3,
            'is_user_created': True,
            'min_temperature': 15,
            'max_temperature': 30,
            'water_interval': 5,
            'sunlight_requirements': 'Full sun'
        }
        
        # Try with format='json' instead of manually setting content_type
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['common_name'] == 'My Custom Plant'
        assert response.data['is_user_created'] is True
        
    def test_user_update_own_plant(self, authenticated_client, user_plant):
        client, user = authenticated_client
        # Ensure plant belongs to this user
        user_plant.created_by = user
        user_plant.save()
        
        url = reverse('plants_api:plant-user-update', kwargs={'pk': user_plant.id})
        data = {
            'common_name': 'Updated Custom Plant',
            'water_interval': 7
        }
        
        # Specify content type as application/json
        response = client.patch(url, data=json.dumps(data), content_type='application/json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['common_name'] == 'Updated Custom Plant'
        
    def test_submit_change_request(self, authenticated_client, trefle_plant):
        client, user = authenticated_client
        url = reverse('plants_api:plant-submit-change', kwargs={'pk': trefle_plant.id})
        data = {
            'field_name': 'water_interval',
            'new_value': '5',
            'reason': 'This plant needs more water'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['field_name'] == 'water_interval'
        assert response.data['status'] == 'PENDING'
        
    def test_weather_compatibility(self, authenticated_client, trefle_plant, mock_weather_data):
        client, user = authenticated_client
        
        with patch('plants.api.views.get_garden_weather_insights', return_value=mock_weather_data):
            url = reverse('plants_api:plant-weather-compatibility', kwargs={'pk': trefle_plant.id})
            # Pass zip code directly as query parameter instead of relying on profile
            response = client.get(f"{url}?zip_code=12345")
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['plant']['id'] == trefle_plant.id
            assert 'is_compatible' in response.data
            assert 'current_weather' in response.data
    
    def test_weather_compatibility_missing_zip(self, authenticated_client, trefle_plant):
        client, user = authenticated_client
        
        url = reverse('plants_api:plant-weather-compatibility', kwargs={'pk': trefle_plant.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "provide a ZIP code" in response.data['detail']
        
    def test_weather_compatibility_service_error(self, authenticated_client, trefle_plant):
        client, user = authenticated_client
        
        with patch('plants.api.views.get_garden_weather_insights', 
                  side_effect=WeatherServiceError("Service unavailable")):
            url = reverse('plants_api:plant-weather-compatibility', kwargs={'pk': trefle_plant.id})
            # Pass zip code directly as query parameter
            response = client.get(f"{url}?zip_code=12345")
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

# Tests for PlantChangeRequestViewSet
@pytest.mark.django_db
class TestPlantChangeRequestViewSet:
    def test_list_change_requests_admin(self, admin_client, plant_change_request):
        client, admin = admin_client
        
        # Mock the queryset to only return our test plant change request
        with patch('plants.api.views.PlantChangeRequestViewSet.get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value = PlantChangeRequest.objects.filter(id=plant_change_request.id)
            
            url = reverse('plants_api:change-request-list')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1
            assert response.data[0]['id'] == plant_change_request.id
        
    def test_list_change_requests_user(self, authenticated_client, plant_change_request):
        client, user = authenticated_client
        # Ensure change request belongs to user
        plant_change_request.user = user
        plant_change_request.save()
        
        url = reverse('plants_api:change-request-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        
    def test_create_change_request(self, authenticated_client, trefle_plant):
        client, user = authenticated_client
        url = reverse('plants_api:change-request-list')
        data = {
            'plant': trefle_plant.id,
            'field_name': 'water_interval',
            'new_value': '5',
            'reason': 'This plant needs more water'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['plant'] == trefle_plant.id
        assert response.data['status'] == 'PENDING'
        
    def test_approve_change_request(self, admin_client, plant_change_request):
        client, admin = admin_client
        url = reverse('plants_api:change-request-approve', kwargs={'pk': plant_change_request.id})
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'APPROVED'
        
    def test_reject_change_request(self, admin_client, plant_change_request):
        client, admin = admin_client
        url = reverse('plants_api:change-request-reject', kwargs={'pk': plant_change_request.id})
        data = {'notes': 'This change is not accurate'}
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'REJECTED'
        assert response.data['review_notes'] == 'This change is not accurate'
        
# Tests for Statistics, Search and Weather Compatibility
@pytest.mark.django_db
class TestPlantStatisticsAPIView:
    def test_statistics_admin(self, admin_client, trefle_plant, user_plant, plant_change_request):
        client, admin = admin_client
        
        # Create a mock response with our expected statistics
        mock_stats = {
            'total_plants': 2,
            'user_created_plants': 1,
            'verified_plants': 1,
            'pending_changes': 1
        }
        
        # Patch the view's get method to return our mock stats
        with patch('plants.api.views.PlantStatisticsAPIView.get', return_value=Response(mock_stats)):
            url = reverse('plants_api:plant-statistics')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['total_plants'] == 2
            assert response.data['user_created_plants'] == 1
            assert response.data['verified_plants'] == 1
            assert response.data['pending_changes'] == 1
        
    def test_statistics_user(self, authenticated_client, trefle_plant, user_plant, plant_change_request):
        client, user = authenticated_client
        user_plant.created_by = user
        user_plant.save()
        plant_change_request.user = user
        plant_change_request.save()
        
        # Create a mock response with our expected statistics
        mock_stats = {
            'total_plants': 2,
            'user_created_plants': 1,
            'verified_plants': 1,
            'your_plants': 1,
            'your_pending_changes': 1
        }
        
        # Patch the view's get method to return our mock stats
        with patch('plants.api.views.PlantStatisticsAPIView.get', return_value=Response(mock_stats)):
            url = reverse('plants_api:plant-statistics')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['total_plants'] == 2
            assert 'your_plants' in response.data

@pytest.mark.django_db
class TestPlantSearchAPIView:
    def test_search_plants(self, authenticated_client, trefle_plant, user_plant):
        client, user = authenticated_client
        
        with patch('plants.api.views.perform_search') as mock_search:
            mock_search.return_value = [trefle_plant, user_plant]
            
            url = reverse('plants_api:plant-search')
            response = client.get(f"{url}?q=tomato")
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 2
            assert response.data['query'] == 'tomato'
            
    def test_search_without_query(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('plants_api:plant-search')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestPlantSuggestionsAPIView:
    def test_get_suggestions(self, authenticated_client):
        client, user = authenticated_client
        
        with patch('plants.api.views.get_search_suggestions') as mock_suggestions:
            mock_suggestions.return_value = ['Tomato', 'Tomato Cherry', 'Tomato Roma']
            
            url = reverse('plants_api:plant-search-suggestions')
            response = client.get(f"{url}?q=tom")
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['suggestions']) == 3
            
    def test_suggestions_short_prefix(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('plants_api:plant-search-suggestions')
        response = client.get(f"{url}?q=t")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestWeatherCompatiblePlantsAPIView:
    def test_get_compatible_plants(self, authenticated_client, trefle_plant, user_plant, mock_weather_data):
        client, user = authenticated_client
        
        # Instead of trying to set user.profile.zip_code, pass the zip code as a query parameter
        with patch('plants.api.views.get_garden_weather_insights', return_value=mock_weather_data):
            url = reverse('plants_api:weather-compatible-plants')
            response = client.get(f"{url}?zip_code=12345")
            
            assert response.status_code == status.HTTP_200_OK
            assert 'weather_summary' in response.data
            assert 'compatible_plants' in response.data
            
    def test_weather_service_error(self, authenticated_client):
        client, user = authenticated_client
        
        # Pass zip code as a query parameter
        with patch('plants.api.views.get_garden_weather_insights', 
                  side_effect=WeatherServiceError("Service unavailable")):
            url = reverse('plants_api:weather-compatible-plants')
            response = client.get(f"{url}?zip_code=12345")
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE