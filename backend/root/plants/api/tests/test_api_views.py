import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.db.models import Q

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
                "image_url": "http://example.com/image1.jpg"
            },
            {
                "id": 2,
                "common_name": "Test Plant 2",
                "scientific_name": "Testus plantus 2",
                "image_url": "http://example.com/image2.jpg"
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
            "family": "Testaceae",
            "genus": "Testus",
            "image_url": "http://example.com/image1.jpg",
            "vegetable": True,
            "edible": True
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

# Plant fixtures
@pytest.fixture
def trefle_plant(db):
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
        sunlight_requirements="Full sun to part shade"
    )
    return plant

@pytest.fixture
def user_plant(db, regular_user):
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
        sunlight_requirements="Full sun"
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
        with patch('plants.api.views.list_plants', return_value=mock_trefle_plants_response):
            url = reverse('plants_api:trefle-list-plants')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['data']) == 2
            assert response.data['data'][0]['common_name'] == "Test Plant 1"
            
    def test_get_plants_with_search(self, client, mock_trefle_plants_response):
        with patch('plants.api.views.list_plants', return_value=mock_trefle_plants_response) as mock_list:
            url = reverse('plants_api:trefle-list-plants')
            response = client.get(f"{url}?q=tomato")
            
            assert response.status_code == status.HTTP_200_OK
            mock_list.assert_called_once()
            assert mock_list.call_args[1]['filters'].get('q') == 'tomato'
            
    def test_get_plants_error(self, client):
        with patch('plants.api.views.list_plants', side_effect=Exception("API Error")):
            url = reverse('plants_api:trefle-list-plants')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to retrieve plant list" in response.data['error']

@pytest.mark.django_db
class TestRetrievePlantAPIView:
    def test_retrieve_plant_success(self, client, mock_trefle_plant_detail_response):
        with patch('plants.api.views.retrieve_plants', return_value=mock_trefle_plant_detail_response):
            url = reverse('plants_api:trefle-retrieve-plant', kwargs={'id': '1'})
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['data']['common_name'] == "Test Plant 1"
            
    def test_retrieve_plant_not_found(self, client):
        with patch('plants.api.views.retrieve_plants', return_value={'data': None}):
            url = reverse('plants_api:trefle-retrieve-plant', kwargs={'id': '999'})
            response = client.get(url)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND

# Tests for PlantViewSet
@pytest.mark.django_db
class TestPlantViewSet:
    def test_list_plants(self, client, trefle_plant, user_plant):
        url = reverse('plants_api:plant-list')
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
            'edible': True
        }
        
        response = client.post(url, data, format='json')
        
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
        url = reverse('plants_api:plant-create-custom')
        data = {
            'common_name': 'My Custom Plant',
            'scientific_name': 'Customus plantus',
            'family': 'Customaceae',
            'genus': 'Customus',
            'vegetable': True,
            'edible': True
        }
        
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
        
        response = client.patch(url, data, format='json')
        
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
        # Mock user profile with zip code
        user.profile.zip_code = '12345'
        user.profile.save()
        
        with patch('plants.api.views.get_garden_weather_insights', return_value=mock_weather_data):
            url = reverse('plants_api:plant-weather-compatibility', kwargs={'pk': trefle_plant.id})
            response = client.get(url)
            
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
        user.profile.zip_code = '12345'
        user.profile.save()
        
        with patch('plants.api.views.get_garden_weather_insights', 
                  side_effect=WeatherServiceError("Service unavailable")):
            url = reverse('plants_api:plant-weather-compatibility', kwargs={'pk': trefle_plant.id})
            response = client.get(url)
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

# Tests for PlantChangeRequestViewSet
@pytest.mark.django_db
class TestPlantChangeRequestViewSet:
    def test_list_change_requests_admin(self, admin_client, plant_change_request):
        client, admin = admin_client
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
        assert response.data['notes'] == 'This change is not accurate'

# Tests for Statistics, Search and Weather Compatibility
@pytest.mark.django_db
class TestPlantStatisticsAPIView:
    def test_statistics_admin(self, admin_client, trefle_plant, user_plant, plant_change_request):
        client, admin = admin_client
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
        user.profile.zip_code = '12345'
        user.profile.save()
        
        with patch('plants.api.views.get_garden_weather_insights', return_value=mock_weather_data):
            url = reverse('plants_api:weather-compatible-plants')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'weather_summary' in response.data
            assert 'compatible_plants' in response.data
            
    def test_weather_service_error(self, authenticated_client):
        client, user = authenticated_client
        user.profile.zip_code = '12345'
        user.profile.save()
        
        with patch('plants.api.views.get_garden_weather_insights', 
                  side_effect=WeatherServiceError("Service unavailable")):
            url = reverse('plants_api:weather-compatible-plants')
            response = client.get(url)
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE