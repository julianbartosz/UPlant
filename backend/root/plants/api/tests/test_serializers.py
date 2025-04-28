import pytest
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock, patch
from rest_framework.exceptions import ValidationError

from plants.models import Plant, PlantChangeRequest
from plants.api.serializers import (
    UserMinimalSerializer, 
    PlantBaseSerializer,
    PlantDetailSerializer, 
    UserPlantCreateSerializer,
    UserPlantUpdateSerializer, 
    AdminPlantSerializer,
    PlantChangeRequestSerializer, 
    PlantChangeRequestCreateSerializer,
    PlantListResponseSerializer,
    TreflePlantSerializer,
    TreflePlantListResponseSerializer
)

User = get_user_model()

# ============= Fixtures =============

@pytest.fixture
def request_factory():
    return APIRequestFactory()

@pytest.fixture
def admin_request(admin_user, request_factory):
    request = request_factory.get('/')
    request.user = admin_user
    return request

@pytest.fixture
def user_request(regular_user, request_factory):
    request = request_factory.get('/')
    request.user = regular_user
    return request

@pytest.fixture
def moderator_user(db):
    user = User.objects.create_user(
        username='moderator',
        email='moderator@example.com',
        password='password123'
    )
    user.role = 'Moderator'
    user.save()
    return user

@pytest.fixture
def moderator_request(moderator_user, request_factory):
    request = request_factory.get('/')
    request.user = moderator_user
    return request

@pytest.fixture
def trefle_plant(db, admin_user):
    """Create a verified plant from Trefle API"""
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
        created_by=admin_user
    )
    return plant

@pytest.fixture
def user_plant(db, regular_user):
    """Create a user-submitted plant"""
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
def pending_change_request(db, trefle_plant, regular_user):
    """Create a pending change request"""
    return PlantChangeRequest.objects.create(
        plant=trefle_plant,
        user=regular_user,
        field_name="water_interval",
        old_value="3",
        new_value="4",
        reason="Basil needs less frequent watering",
        status="PENDING"
    )

@pytest.fixture
def approved_change_request(db, trefle_plant, regular_user, admin_user):
    """Create an approved change request"""
    return PlantChangeRequest.objects.create(
        plant=trefle_plant,
        user=regular_user,
        field_name="min_temperature",
        old_value="10",
        new_value="12",
        reason="Basil is more cold sensitive",
        status="APPROVED",
        reviewer=admin_user,
        review_notes="Confirmed with external sources"
    )

@pytest.fixture
def trefle_api_data():
    """Sample data from Trefle API"""
    return {
        "data": [
            {
                "id": 1,
                "common_name": "Basil",
                "scientific_name": "Ocimum basilicum",
                "slug": "ocimum-basilicum",
                "status": "accepted",
                "rank": "species",
                "family_common_name": "Mint family",
                "family": "Lamiaceae",
                "genus_id": 664,
                "genus": "Ocimum",
                "image_url": "https://bs.plantnet.org/image/o/abc123",
                "synonyms": ["Ocimum basilicum var. glabratum"],
                "links": {
                    "self": "/api/v1/species/ocimum-basilicum",
                    "plant": "/api/v1/plants/ocimum-basilicum"
                }
            }
        ],
        "links": {
            "self": "/api/v1/plants?page=1",
            "next": "/api/v1/plants?page=2"
        },
        "meta": {
            "total": 100
        }
    }

# ============= Tests =============

@pytest.mark.django_db
class TestUserMinimalSerializer:
    """Tests for the UserMinimalSerializer"""
    
    def test_serialization(self, regular_user):
        """Test serializing a user"""
        serializer = UserMinimalSerializer(regular_user)
        data = serializer.data
        
        assert data['id'] == regular_user.id
        assert data['username'] == regular_user.username
        assert data['email'] == regular_user.email
        
        # Ensure no other fields are included
        assert len(data) == 3

@pytest.mark.django_db
class TestPlantBaseSerializer:
    """Tests for the PlantBaseSerializer"""
    
    def test_serialization_with_created_by(self, trefle_plant):
        """Test serializing a plant with creator"""
        serializer = PlantBaseSerializer(trefle_plant)
        data = serializer.data
        
        assert data['id'] == trefle_plant.id
        assert data['common_name'] == "Basil"
        assert data['scientific_name'] == "Ocimum basilicum"
        assert data['family'] == "Lamiaceae"
        assert data['image_url'] == "http://example.com/basil.jpg"
        assert data['is_user_created'] is False
        assert data['is_verified'] is True
        assert data['created_by'] == trefle_plant.created_by.id
        assert data['created_by_username'] == trefle_plant.created_by.username
        
    def test_serialization_without_created_by(self, trefle_plant):
        """Test serializing a plant without creator"""
        trefle_plant.created_by = None
        trefle_plant.save()
        
        serializer = PlantBaseSerializer(trefle_plant)
        data = serializer.data
        
        assert data['created_by'] is None
        assert data['created_by_username'] is None
        
    def test_read_only_fields(self, trefle_plant):
        """Test read-only fields cannot be updated"""
        serializer = PlantBaseSerializer(data={
            'id': 999,
            'common_name': 'New Basil',
            'scientific_name': 'New basilicum',
            'created_at': '2023-01-01T00:00:00Z'
        }, instance=trefle_plant, partial=True)
        
        assert serializer.is_valid()
        # ID and created_at should be ignored in validated_data
        assert 'id' not in serializer.validated_data
        assert 'created_at' not in serializer.validated_data

@pytest.mark.django_db
class TestPlantDetailSerializer:
    """Tests for the PlantDetailSerializer"""
    
    def test_serialization(self, trefle_plant):
        """Test full plant serialization"""
        serializer = PlantDetailSerializer(trefle_plant)
        data = serializer.data
        
        assert data['id'] == trefle_plant.id
        assert data['common_name'] == "Basil"
        assert data['scientific_name'] == "Ocimum basilicum"
        assert data['api_id'] == "123456"
        assert data['family'] == "Lamiaceae"
        assert data['vegetable'] is False
        assert data['edible'] is True
        assert data['min_temperature'] == 10
        assert data['max_temperature'] == 35
        assert data['sunlight_requirements'] == "Full sun to part shade"
        assert 'pending_changes' in data
        
    def test_pending_changes_admin_view(self, trefle_plant, pending_change_request, admin_request):
        """Test that admins see all pending changes"""
        serializer = PlantDetailSerializer(trefle_plant, context={'request': admin_request})
        data = serializer.data
        
        assert len(data['pending_changes']) == 1
        assert data['pending_changes'][0]['id'] == pending_change_request.id
        assert data['pending_changes'][0]['status'] == 'PENDING'
        
    def test_pending_changes_moderator_view(self, trefle_plant, pending_change_request, moderator_request):
        """Test that moderators see all pending changes"""
        serializer = PlantDetailSerializer(trefle_plant, context={'request': moderator_request})
        data = serializer.data
        
        assert len(data['pending_changes']) == 1
        assert data['pending_changes'][0]['id'] == pending_change_request.id
        
    def test_pending_changes_user_view_own_changes(self, trefle_plant, pending_change_request, user_request):
        """Test that users see only their own pending changes"""
        # Make sure the change request is owned by the user in the request
        pending_change_request.user = user_request.user
        pending_change_request.save()
        
        serializer = PlantDetailSerializer(trefle_plant, context={'request': user_request})
        data = serializer.data
        
        assert len(data['pending_changes']) == 1
        assert data['pending_changes'][0]['id'] == pending_change_request.id
        
    def test_pending_changes_user_view_others_changes(self, trefle_plant, pending_change_request, user_request, admin_user):
        """Test that users don't see others' pending changes"""
        # Make sure the change request is NOT owned by the user in the request
        pending_change_request.user = admin_user
        pending_change_request.save()
        
        serializer = PlantDetailSerializer(trefle_plant, context={'request': user_request})
        data = serializer.data
        
        assert len(data['pending_changes']) == 0
        
    def test_pending_changes_anonymous(self, trefle_plant, pending_change_request, request_factory):
        """Test that anonymous users see no pending changes"""
        request = request_factory.get('/')  # Anonymous request
        request.user = MagicMock(is_authenticated=False)
        
        serializer = PlantDetailSerializer(trefle_plant, context={'request': request})
        data = serializer.data
        
        assert len(data['pending_changes']) == 0

@pytest.mark.django_db
class TestUserPlantCreateSerializer:
    """Tests for the UserPlantCreateSerializer"""
    
    def test_create_valid_plant(self, user_request):
        """Test creating a valid custom plant"""
        data = {
            'common_name': 'My Custom Rose',
            'scientific_name': 'Rosa custom',
            'water_interval': 2,
            'sunlight_requirements': 'Full sun',
            'soil_type': 'Well-draining',
            'min_temperature': 5,
            'max_temperature': 30,
            'detailed_description': 'My beautiful rose plant',
            'care_instructions': 'Water regularly'
        }
        
        serializer = UserPlantCreateSerializer(data=data, context={'request': user_request})
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Mock the create_user_plant method to avoid actual DB operations
        with patch.object(Plant, 'create_user_plant', return_value=Plant(**data)):
            plant = serializer.save()
            
            assert plant.common_name == 'My Custom Rose'
            assert plant.scientific_name == 'Rosa custom'
            assert plant.water_interval == 2
            
    def test_required_fields_validation(self, user_request):
        """Test validation of required fields"""
        # Missing required fields
        data = {
            'common_name': 'Incomplete Plant',
            # missing scientific_name and other required fields
        }
        
        serializer = UserPlantCreateSerializer(data=data, context={'request': user_request})
        assert not serializer.is_valid()
        
        # Check that error messages mention missing required fields
        for field in Plant.USER_REQUIRED_FIELDS:
            if field not in data:
                assert field in serializer.errors
                
    def test_temperature_range_validation(self, user_request):
        """Test validation of temperature ranges"""
        data = {
            'common_name': 'Invalid Temp Plant',
            'scientific_name': 'Tempus invalidus',
            'water_interval': 3,
            'sunlight_requirements': 'Partial shade',
            'soil_type': 'Loamy',
            'min_temperature': 30,  # Higher than max
            'max_temperature': 20,
            'detailed_description': 'A plant with invalid temperature range',
            'care_instructions': 'Keep cool'
        }
        
        serializer = UserPlantCreateSerializer(data=data, context={'request': user_request})
        assert not serializer.is_valid()
        assert 'min_temperature' in serializer.errors
        assert 'max_temperature' in serializer.errors

@pytest.mark.django_db
class TestUserPlantUpdateSerializer:
    """Tests for the UserPlantUpdateSerializer"""
    
    def test_update_user_plant(self, user_plant, user_request):
        """Test updating a user's own plant"""
        data = {
            'common_name': 'Updated Tomato Plant',
            'water_interval': 4,
            'detailed_description': 'Updated description'
        }
        
        serializer = UserPlantUpdateSerializer(
            instance=user_plant, 
            data=data, 
            partial=True,
            context={'request': user_request}
        )
        
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Mock the save method to avoid actual DB operations
        with patch.object(Plant, 'save'):
            updated_plant = serializer.save()
            assert updated_plant.common_name == 'Updated Tomato Plant'
            assert updated_plant.water_interval == 4
            assert updated_plant.detailed_description == 'Updated description'
            
    def test_temperature_range_validation(self, user_plant, user_request):
        """Test validation of temperature range during updates"""
        data = {
            'min_temperature': 40,
            'max_temperature': 30
        }
        
        serializer = UserPlantUpdateSerializer(
            instance=user_plant, 
            data=data, 
            partial=True,
            context={'request': user_request}
        )
        
        assert not serializer.is_valid()
        assert 'min_temperature' in serializer.errors
        assert 'max_temperature' in serializer.errors
        
    def test_prevent_trefle_plant_edit(self, trefle_plant, user_request):
        """Test that regular users cannot edit Trefle plants directly"""
        data = {
            'common_name': 'Hacked Basil',
            'water_interval': 99
        }
        
        serializer = UserPlantUpdateSerializer(
            instance=trefle_plant, 
            data=data, 
            partial=True,
            context={'request': user_request}
        )
        
        assert not serializer.is_valid()
        # Should have a general error about not being able to edit Trefle plants
        assert any("change request" in str(error) for error in serializer.errors.values())
        
    def test_admin_can_edit_trefle_plant(self, trefle_plant, admin_request):
        """Test that admins can edit Trefle plants directly"""
        data = {
            'common_name': 'Admin Updated Basil',
            'water_interval': 5
        }
        
        serializer = UserPlantUpdateSerializer(
            instance=trefle_plant, 
            data=data, 
            partial=True,
            context={'request': admin_request}
        )
        
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Mock the save method to avoid actual DB operations
        with patch.object(Plant, 'save'):
            updated_plant = serializer.save()
            assert updated_plant.common_name == 'Admin Updated Basil'
            assert updated_plant.water_interval == 5

@pytest.mark.django_db
class TestAdminPlantSerializer:
    """Tests for the AdminPlantSerializer"""
    
    def test_serialization(self, trefle_plant):
        """Test serializing a plant with all fields"""
        serializer = AdminPlantSerializer(trefle_plant)
        data = serializer.data
        
        assert data['id'] == trefle_plant.id
        assert data['common_name'] == "Basil"
        assert data['scientific_name'] == "Ocimum basilicum"
        # Check that all fields are included
        assert len(data) > 15
        
    def test_create_plant(self):
        """Test creating a new plant as admin"""
        data = {
            'common_name': 'Admin Created Plant',
            'scientific_name': 'Adminus createus',
            'family': 'Adminaceae',
            'genus': 'Adminus',
            'vegetable': True,
            'edible': True,
            'is_verified': True,
            'api_id': None  # Not from Trefle
        }
        
        serializer = AdminPlantSerializer(data=data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        with patch.object(Plant, 'save'):  # Mock to avoid actual DB operations
            plant = serializer.save()
            assert plant.common_name == 'Admin Created Plant'
            assert plant.scientific_name == 'Adminus createus'
            assert plant.is_verified is True

@pytest.mark.django_db
class TestPlantChangeRequestSerializer:
    """Tests for the PlantChangeRequestSerializer"""
    
    def test_serialization(self, pending_change_request):
        """Test serializing a change request"""
        serializer = PlantChangeRequestSerializer(pending_change_request)
        data = serializer.data
        
        assert data['id'] == pending_change_request.id
        assert data['field_name'] == 'water_interval'
        assert data['old_value'] == '3'
        assert data['new_value'] == '4'
        assert data['reason'] == 'Basil needs less frequent watering'
        assert data['status'] == 'PENDING'
        
        # Check related objects
        assert 'user_details' in data
        assert data['user_details']['username'] == pending_change_request.user.username
        assert 'plant_details' in data
        assert data['plant_details']['common_name'] == pending_change_request.plant.common_name
        
    def test_create_change_request(self, trefle_plant, user_request):
        """Test creating a change request"""
        data = {
            'plant': trefle_plant.id,
            'field_name': 'sunlight_requirements',
            'new_value': 'Partial shade',
            'reason': 'Basil grows well in partial shade too'
        }
        
        serializer = PlantChangeRequestSerializer(
            data=data, 
            context={'request': user_request}
        )
        
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Mock creation to avoid actual DB operations
        with patch.object(PlantChangeRequest, 'save'):
            change_request = serializer.save()
            assert change_request.plant == trefle_plant
            assert change_request.field_name == 'sunlight_requirements'
            assert change_request.new_value == 'Partial shade'
            assert change_request.user == user_request.user  # Should be set from context
            assert change_request.old_value == trefle_plant.sunlight_requirements  # Should be captured
            
    def test_validate_editable_fields(self, trefle_plant, user_request):
        """Test that only editable fields can be changed"""
        data = {
            'plant': trefle_plant.id,
            'field_name': 'is_verified',  # Not user-editable
            'new_value': 'False',
            'reason': 'Testing non-editable field'
        }
        
        serializer = PlantChangeRequestSerializer(
            data=data, 
            context={'request': user_request}
        )
        
        assert not serializer.is_valid()
        assert 'field_name' in serializer.errors
        assert "cannot be edited by users" in str(serializer.errors['field_name'])

@pytest.mark.django_db
class TestPlantChangeRequestCreateSerializer:
    """Tests for the simplified PlantChangeRequestCreateSerializer"""
    
    def test_create_valid_request(self, trefle_plant, user_request):
        """Test creating a valid change request"""
        data = {
            'plant': trefle_plant.id,
            'field_name': 'water_interval',
            'new_value': '5',
            'reason': 'Testing valid request'
        }
        
        serializer = PlantChangeRequestCreateSerializer(data=data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
    def test_invalid_field_name(self, trefle_plant, user_request):
        """Test validation of field name"""
        data = {
            'plant': trefle_plant.id,
            'field_name': 'created_at',  # Not editable
            'new_value': '2023-01-01',
            'reason': 'Testing invalid field'
        }
        
        serializer = PlantChangeRequestCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'field_name' in serializer.errors
        
    def test_user_created_plant_restriction(self, user_plant, user_request):
        """Test that change requests are only for Trefle plants"""
        data = {
            'plant': user_plant.id,
            'field_name': 'water_interval',
            'new_value': '7',
            'reason': 'Testing with user plant'
        }
        
        serializer = PlantChangeRequestCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert any("User plants can be edited directly" in str(error) for error in serializer.errors.values())

@pytest.mark.django_db
class TestPlantListResponseSerializer:
    """Tests for the PlantListResponseSerializer"""
    
    def test_serialization(self, trefle_plant, user_plant):
        """Test serializing a list response"""
        plants = [trefle_plant, user_plant]
        
        # Manually create the structure expected by PlantListResponseSerializer
        data = {
            'data': PlantBaseSerializer(plants, many=True).data,
            'links': {
                'self': '/api/plants?page=1',
                'next': '/api/plants?page=2'
            },
            'meta': {
                'total': 2,
                'page': 1
            }
        }
        
        serializer = PlantListResponseSerializer(data=data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Check that the structure is preserved
        assert len(serializer.validated_data['data']) == 2
        assert serializer.validated_data['links']['next'] == '/api/plants?page=2'
        assert serializer.validated_data['meta']['total'] == 2

@pytest.mark.django_db
class TestTreflePlantSerializer:
    """Tests for the TreflePlantSerializer"""
    
    def test_serialization(self, trefle_api_data):
        """Test deserializing Trefle API data"""
        plant_data = trefle_api_data['data'][0]
        
        serializer = TreflePlantSerializer(data=plant_data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        validated_data = serializer.validated_data
        assert validated_data['id'] == 1
        assert validated_data['common_name'] == 'Basil'
        assert validated_data['scientific_name'] == 'Ocimum basilicum'
        assert validated_data['family'] == 'Lamiaceae'
        assert validated_data['genus'] == 'Ocimum'
        assert validated_data['image_url'] == 'https://bs.plantnet.org/image/o/abc123'
        
    def test_missing_optional_fields(self):
        """Test deserializing with missing optional fields"""
        data = {
            'id': 2,
            'slug': 'plant-slug',
            'scientific_name': 'Scientific Name',
            'status': 'accepted',
            'rank': 'species',
            'family': 'Family Name',
            'genus_id': 123,
            'genus': 'Genus'
            # Missing optional fields like common_name, image_url
        }
        
        serializer = TreflePlantSerializer(data=data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Check that optional fields are None
        assert serializer.validated_data['common_name'] is None
        assert 'image_url' not in serializer.validated_data

@pytest.mark.django_db
class TestTreflePlantListResponseSerializer:
    """Tests for the TreflePlantListResponseSerializer"""
    
    def test_serialization(self, trefle_api_data):
        """Test deserializing Trefle API list response"""
        serializer = TreflePlantListResponseSerializer(data=trefle_api_data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        validated_data = serializer.validated_data
        assert len(validated_data['data']) == 1
        assert validated_data['data'][0]['id'] == 1
        assert validated_data['links']['self'] == '/api/v1/plants?page=1'
        assert validated_data['links']['next'] == '/api/v1/plants?page=2'
        assert validated_data['meta']['total'] == 100
        
    def test_minimal_response(self):
        """Test deserializing minimal response with just data"""
        data = {
            'data': []
            # Missing links and meta
        }
        
        serializer = TreflePlantListResponseSerializer(data=data)
        assert serializer.is_valid(), f"Errors: {serializer.errors}"