import pytest
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import serializers

from django.contrib.auth import get_user_model
from gardens.models import Garden, GardenLog, PlantHealthStatus
from gardens.api.serializers import GardenSerializer, GardenLogSerializer, GardenGridSerializer
from plants.models import Plant

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
        password='password123'
    )

@pytest.fixture
def test_plant():
    return Plant.objects.create(
        common_name="Test Plant",
        scientific_name="Testus plantus",
        is_user_created=False,
        slug="testus-plantus",
        family="Test Family"
    )

@pytest.fixture
def second_plant():
    return Plant.objects.create(
        common_name="Second Plant",
        scientific_name="Testus secundus",
        is_user_created=False,
        slug="testus-secundus",
        family="Test Family"
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
def small_garden(user):
    return Garden.objects.create(
        user=user,
        name="Small Garden",
        size_x=2,
        size_y=2
    )

@pytest.fixture
def unnamed_garden(user):
    return Garden.objects.create(
        user=user,
        size_x=3,
        size_y=3
    )

@pytest.fixture
def other_garden(other_user):
    return Garden.objects.create(
        user=other_user,
        name="Other Garden",
        size_x=4,
        size_y=4
    )

@pytest.fixture
def garden_log(garden, test_plant):
    return GardenLog.objects.create(
        garden=garden,
        plant=test_plant,
        x_coordinate=1,
        y_coordinate=1,
        planted_date=timezone.now().date(),
        notes="Test notes",
        health_status=PlantHealthStatus.GOOD
    )

@pytest.fixture
def garden_with_logs(garden, test_plant, second_plant):
    # Create some logs for testing
    log1 = GardenLog.objects.create(
        garden=garden,
        plant=test_plant,
        x_coordinate=1,
        y_coordinate=1,
        planted_date=timezone.now().date(),
        health_status=PlantHealthStatus.GOOD
    )
    
    log2 = GardenLog.objects.create(
        garden=garden,
        plant=second_plant,
        x_coordinate=3,
        y_coordinate=2,
        planted_date=timezone.now().date() - timedelta(days=10),
        health_status=PlantHealthStatus.EXCELLENT
    )
    
    return garden

@pytest.fixture
def mock_request(user):
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    return MockRequest(user)

@pytest.fixture
def complete_garden_log(garden, test_plant):
    """Create a garden log with all fields populated"""
    return GardenLog.objects.create(
        garden=garden,
        plant=test_plant,
        x_coordinate=2,
        y_coordinate=2,
        planted_date=timezone.now().date(),
        notes="Detailed notes",
        health_status=PlantHealthStatus.EXCELLENT,
        last_watered=timezone.now() - timedelta(days=1),
        last_fertilized=timezone.now() - timedelta(days=5),
        last_pruned=timezone.now() - timedelta(days=10),
        growth_stage="MATURE"
    )

# ==================== TEST CLASSES ====================

@pytest.mark.django_db
class TestGardenLogSerializer:
    """Tests for the GardenLogSerializer"""
    
    def test_serialization_basic(self, garden_log):
        """Test basic serialization of a garden log"""
        serializer = GardenLogSerializer(garden_log)
        data = serializer.data
        
        # Verify required fields
        assert data['id'] == garden_log.id
        assert data['garden'] == garden_log.garden.id
        assert data['plant'] == garden_log.plant.id
        assert data['x_coordinate'] == garden_log.x_coordinate
        assert data['y_coordinate'] == garden_log.y_coordinate
        assert data['planted_date'] == garden_log.planted_date.isoformat()
        assert data['notes'] == garden_log.notes
        assert data['health_status'] == garden_log.health_status
    
    def test_serialization_with_plant_details(self, garden_log):
        """Test that plant_details are included and correct"""
        serializer = GardenLogSerializer(garden_log)
        data = serializer.data
        
        # Check plant_details nested object
        assert 'plant_details' in data
        assert data['plant_details']['id'] == garden_log.plant.id
        assert data['plant_details']['common_name'] == garden_log.plant.common_name
        assert data['plant_details']['scientific_name'] == garden_log.plant.scientific_name
    
    def test_serialization_all_fields(self, complete_garden_log):
        """Test serialization including optional fields"""
        serializer = GardenLogSerializer(complete_garden_log)
        data = serializer.data
        
        # Check all fields are present
        assert data['last_watered'] is not None
        assert data['last_fertilized'] is not None
        assert data['last_pruned'] is not None
        assert data['growth_stage'] == "MATURE"
    
    def test_create_garden_log(self, garden, test_plant):
        """Test creating a garden log through serializer"""
        data = {
            'garden': garden.id,
            'plant': test_plant.id,
            'x_coordinate': 2,
            'y_coordinate': 3,
            'planted_date': timezone.now().date().isoformat(),
            'notes': "Test notes"
        }
        
        serializer = GardenLogSerializer(data=data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        garden_log = serializer.save()
        assert garden_log.garden_id == garden.id
        assert garden_log.plant_id == test_plant.id
        assert garden_log.x_coordinate == 2
        assert garden_log.y_coordinate == 3
        assert garden_log.notes == "Test notes"
    
    def test_update_garden_log(self, garden_log, second_plant):
        """Test updating a garden log through serializer"""
        data = {
            'garden': garden_log.garden.id,
            'plant': second_plant.id,  # Change plant
            'x_coordinate': garden_log.x_coordinate,
            'y_coordinate': garden_log.y_coordinate,
            'notes': "Updated notes"
        }
        
        serializer = GardenLogSerializer(garden_log, data=data, partial=True)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        updated_log = serializer.save()
        assert updated_log.plant_id == second_plant.id
        assert updated_log.notes == "Updated notes"
    
    def test_validate_garden_required(self, test_plant):
        """Test validation requiring garden"""
        data = {
            'plant': test_plant.id,
            'x_coordinate': 1,
            'y_coordinate': 1,
            'planted_date': timezone.now().date().isoformat()
        }
        
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'garden' in serializer.errors
    
    def test_validate_plant_required(self, garden):
        """Test validation requiring plant"""
        data = {
            'garden': garden.id,
            'x_coordinate': 1,
            'y_coordinate': 1,
            'planted_date': timezone.now().date().isoformat()
        }
        
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'plant' in serializer.errors
    
    def test_validate_coordinates_required(self, garden, test_plant):
        """Test validation requiring coordinates"""
        data = {
            'garden': garden.id,
            'plant': test_plant.id,
            'planted_date': timezone.now().date().isoformat()
        }
        
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'x_coordinate' in serializer.errors
        assert 'y_coordinate' in serializer.errors
    
    def test_validate_x_coordinate_bounds(self, garden, test_plant):
        """Test validation of x coordinate bounds"""
        # Test x coordinate too large
        data = {
            'garden': garden.id,
            'plant': test_plant.id,
            'x_coordinate': garden.size_x,  # Out of bounds (size_x is 5, valid is 0-4)
            'y_coordinate': 1,
            'planted_date': timezone.now().date().isoformat()
        }
        
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'x_coordinate' in serializer.errors
        
        # Test x coordinate negative
        data['x_coordinate'] = -1
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'x_coordinate' in serializer.errors
    
    def test_validate_y_coordinate_bounds(self, garden, test_plant):
        """Test validation of y coordinate bounds"""
        # Test y coordinate too large
        data = {
            'garden': garden.id,
            'plant': test_plant.id,
            'x_coordinate': 1,
            'y_coordinate': garden.size_y,  # Out of bounds (size_y is 5, valid is 0-4)
            'planted_date': timezone.now().date().isoformat()
        }
        
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'y_coordinate' in serializer.errors
        
        # Test y coordinate negative
        data['y_coordinate'] = -1
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'y_coordinate' in serializer.errors
    
    def test_validate_position_unique(self, garden_log, test_plant):
        """Test validation of unique position"""
        # Try to create another log at the same position
        data = {
            'garden': garden_log.garden.id,
            'plant': test_plant.id,
            'x_coordinate': garden_log.x_coordinate,
            'y_coordinate': garden_log.y_coordinate,
            'planted_date': timezone.now().date().isoformat()
        }
        
        serializer = GardenLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'position' in serializer.errors[0]
    
    def test_validate_position_update_same(self, garden_log):
        """Test that updating a log with the same position is allowed"""
        data = {
            'garden': garden_log.garden.id,
            'plant': garden_log.plant.id,
            'x_coordinate': garden_log.x_coordinate,
            'y_coordinate': garden_log.y_coordinate,
            'notes': "Updated notes"
        }
        
        serializer = GardenLogSerializer(garden_log, data=data, partial=True)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
    
    def test_validate_position_update_occupied(self, garden, garden_log, second_plant):
        """Test that updating a log to an occupied position is not allowed"""
        # Create another log
        other_log = GardenLog.objects.create(
            garden=garden,
            plant=second_plant,
            x_coordinate=3,
            y_coordinate=3,
            planted_date=timezone.now().date()
        )
        
        # Try to update the original log to the position of the other log
        data = {
            'garden': garden_log.garden.id,
            'plant': garden_log.plant.id,
            'x_coordinate': other_log.x_coordinate,
            'y_coordinate': other_log.y_coordinate
        }
        
        serializer = GardenLogSerializer(garden_log, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'position' in serializer.errors[0]


@pytest.mark.django_db
class TestGardenSerializer:
    """Tests for the GardenSerializer"""
    
    def test_serialization_basic(self, garden):
        """Test basic serialization of a garden"""
        serializer = GardenSerializer(garden)
        data = serializer.data
        
        # Verify required fields
        assert data['id'] == garden.id
        assert data['name'] == garden.name
        assert data['size_x'] == garden.size_x
        assert data['size_y'] == garden.size_y
        assert data['user'] == garden.user.id
    
    def test_serialization_unnamed_garden(self, unnamed_garden):
        """Test serialization of a garden without name"""
        serializer = GardenSerializer(unnamed_garden)
        data = serializer.data
        
        assert data['name'] is None  # Name should be None if not provided
    
    def test_serialization_with_logs(self, garden_with_logs):
        """Test serialization including garden_logs"""
        serializer = GardenSerializer(garden_with_logs)
        data = serializer.data
        
        # Check garden_logs list
        assert 'garden_logs' in data
        assert len(data['garden_logs']) == 2
        
        # Check total_plants method field
        assert data['total_plants'] == 2
    
    def test_create_garden(self, user, mock_request):
        """Test creating a garden through serializer"""
        data = {
            'name': 'New Garden',
            'size_x': 10,
            'size_y': 8
        }
        
        serializer = GardenSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        garden = serializer.save()
        assert garden.name == 'New Garden'
        assert garden.size_x == 10
        assert garden.size_y == 8
        assert garden.user == user  # User should be assigned from request
    
    def test_update_garden(self, garden):
        """Test updating a garden through serializer"""
        data = {
            'name': 'Updated Garden',
            'size_x': 6
        }
        
        serializer = GardenSerializer(garden, data=data, partial=True)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        updated_garden = serializer.save()
        assert updated_garden.name == 'Updated Garden'
        assert updated_garden.size_x == 6
        assert updated_garden.size_y == garden.size_y  # Unchanged
    
    def test_cannot_update_user(self, garden, other_user, mock_request):
        """Test that user field is read-only and cannot be changed"""
        original_user = garden.user
        
        data = {
            'name': 'Updated Garden',
            'user': other_user.id
        }
        
        serializer = GardenSerializer(garden, data=data, partial=True, context={'request': mock_request})
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        updated_garden = serializer.save()
        assert updated_garden.user == original_user  # User should not change


@pytest.mark.django_db
class TestGardenGridSerializer:
    """Tests for the GardenGridSerializer"""
    
    def test_empty_grid(self, garden):
        """Test serialization of an empty garden grid"""
        serializer = GardenGridSerializer(garden)
        data = serializer.data
        
        # Check fields
        assert data['id'] == garden.id
        assert data['name'] == garden.name
        assert data['x'] == garden.size_x
        assert data['y'] == garden.size_y
        
        # Check grid structure
        assert 'cells' in data
        assert len(data['cells']) == garden.size_y
        assert len(data['cells'][0]) == garden.size_x
        
        # All cells should be None
        for row in data['cells']:
            for cell in row:
                assert cell is None
    
    def test_grid_with_plants(self, garden_with_logs):
        """Test serialization of a garden grid with plants"""
        serializer = GardenGridSerializer(garden_with_logs)
        data = serializer.data
        
        # Check occupied cells
        assert data['cells'][1][1] is not None  # Position (1,1) should have a plant
        assert data['cells'][2][3] is not None  # Position (3,2) should have a plant
        
        # Check cell data structure
        cell = data['cells'][1][1]
        assert cell['id'] is not None
        assert cell['common_name'] is not None
        assert cell['scientific_name'] is not None
        assert cell['family'] is not None
        assert cell['health_status'] is not None
        assert cell['log_id'] is not None
    
    def test_grid_dimensions(self, small_garden, test_plant):
        """Test that grid dimensions match garden size"""
        # Create a small 2x2 garden with one plant
        GardenLog.objects.create(
            garden=small_garden,
            plant=test_plant,
            x_coordinate=1,
            y_coordinate=0,
            planted_date=timezone.now().date()
        )
        
        serializer = GardenGridSerializer(small_garden)
        data = serializer.data
        
        # Check dimensions
        assert data['x'] == 2
        assert data['y'] == 2
        assert len(data['cells']) == 2
        assert len(data['cells'][0]) == 2
        
        # Check the plant location
        assert data['cells'][0][1] is not None  # Position (1,0)
        assert data['cells'][0][0] is None
        assert data['cells'][1][0] is None
        assert data['cells'][1][1] is None
    
    def test_grid_with_plant_at_boundary(self, garden, test_plant):
        """Test that plants at the boundary are displayed correctly"""
        # Create a plant at the edge coordinates (4,4) - max is (4,4) for 5x5 garden
        GardenLog.objects.create(
            garden=garden,
            plant=test_plant,
            x_coordinate=4,
            y_coordinate=4,
            planted_date=timezone.now().date()
        )
        
        serializer = GardenGridSerializer(garden)
        data = serializer.data
        
        # Check that the plant appears in the correct position
        assert data['cells'][4][4] is not None
    
    def test_grid_with_deleted_plant(self, garden_with_logs):
        """Test that deleted plants are not included in the grid"""
        # Get the first log and mark it as deleted
        log = garden_with_logs.logs.first()
        log.is_deleted = True
        log.save()
        
        serializer = GardenGridSerializer(garden_with_logs)
        data = serializer.data
        
        # The cell should be None where the deleted plant was
        assert data['cells'][log.y_coordinate][log.x_coordinate] is None