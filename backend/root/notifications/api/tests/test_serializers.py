import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation, NotifTypes
from notifications.api.serializers import (
    NotificationPlantAssociationSerializer,
    NotificationInstanceSerializer,
    NotificationSerializer,
    DashboardNotificationSerializer
)
from plants.models import Plant
from gardens.models import Garden

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
def garden(user):
    return Garden.objects.create(
        user=user,
        name="Test Garden",
        size_x=5,
        size_y=5
    )

@pytest.fixture
def other_garden(other_user):
    return Garden.objects.create(
        user=other_user,
        name="Other Garden",
        size_x=3,
        size_y=3
    )

@pytest.fixture
def test_plant():
    return Plant.objects.create(
        common_name="Test Plant",
        scientific_name="Testus plantus",
        is_user_created=False,
        slug="testus-plantus"
    )

@pytest.fixture
def second_plant():
    return Plant.objects.create(
        common_name="Second Plant",
        scientific_name="Testus secundus",
        is_user_created=False,
        slug="testus-secundus"
    )

@pytest.fixture
def third_plant():
    return Plant.objects.create(
        common_name="Third Plant",
        scientific_name="Testus tertius",
        is_user_created=False,
        slug="testus-tertius"
    )

@pytest.fixture
def fourth_plant():
    return Plant.objects.create(
        common_name=None,  # Test with no common name
        scientific_name="Testus quartus",
        is_user_created=False,
        slug="testus-quartus"
    )

@pytest.fixture
def water_notification(garden):
    return Notification.objects.create(
        garden=garden,
        name="Water Notification",
        type=NotifTypes.WA,
        interval=7
    )

@pytest.fixture
def other_notification(garden):
    return Notification.objects.create(
        garden=garden,
        name="Custom Notification",
        type=NotifTypes.OT,
        subtype="SPECIAL",
        interval=30
    )

@pytest.fixture
def notification_with_plants(water_notification, test_plant, second_plant, third_plant):
    assoc1 = NotificationPlantAssociation.objects.create(
        notification=water_notification,
        plant=test_plant
    )
    assoc2 = NotificationPlantAssociation.objects.create(
        notification=water_notification,
        plant=second_plant,
        custom_interval=14  # Add custom interval to test this field
    )
    assoc3 = NotificationPlantAssociation.objects.create(
        notification=water_notification,
        plant=third_plant
    )
    return water_notification

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
        next_due=timezone.now() - timedelta(days=3),
        status='PENDING'
    )

@pytest.fixture
def completed_instance(water_notification):
    return NotificationInstance.objects.create(
        notification=water_notification,
        next_due=timezone.now() - timedelta(days=1),
        last_completed=timezone.now() - timedelta(hours=12),
        status='COMPLETED'
    )

@pytest.fixture
def skipped_instance(water_notification):
    return NotificationInstance.objects.create(
        notification=water_notification,
        next_due=timezone.now() - timedelta(days=1),
        status='SKIPPED'
    )

@pytest.fixture
def notification_with_instances(water_notification, pending_instance, overdue_instance, completed_instance):
    return water_notification

@pytest.fixture
def mock_request(user):
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    return MockRequest(user)

# ==================== TEST CLASSES ====================

@pytest.mark.django_db
class TestNotificationPlantAssociationSerializer:
    """Tests for the NotificationPlantAssociationSerializer"""
    
    def test_serialization(self, test_plant, water_notification):
        """Test serializing a plant association"""
        association = NotificationPlantAssociation.objects.create(
            notification=water_notification,
            plant=test_plant,
            custom_interval=10
        )
        
        serializer = NotificationPlantAssociationSerializer(association)
        data = serializer.data
        
        # Check that all expected fields are present
        assert 'id' in data
        assert 'plant' in data
        assert 'plant_details' in data
        assert 'custom_interval' in data
        
        # Check the values
        assert data['plant'] == test_plant.id
        assert data['custom_interval'] == 10
        
        # Check that plant_details contains expected nested data
        assert data['plant_details']['id'] == test_plant.id
        assert data['plant_details']['common_name'] == test_plant.common_name
        assert data['plant_details']['scientific_name'] == test_plant.scientific_name
    
    def test_serialization_without_custom_interval(self, test_plant, water_notification):
        """Test serializing with default interval"""
        association = NotificationPlantAssociation.objects.create(
            notification=water_notification,
            plant=test_plant
        )
        
        serializer = NotificationPlantAssociationSerializer(association)
        data = serializer.data
        
        assert data['custom_interval'] is None


@pytest.mark.django_db
class TestNotificationInstanceSerializer:
    """Tests for the NotificationInstanceSerializer"""
    
    def test_pending_instance_serialization(self, pending_instance):
        """Test serializing a pending notification instance"""
        serializer = NotificationInstanceSerializer(pending_instance)
        data = serializer.data
        
        # Check all expected fields
        assert 'id' in data
        assert 'next_due' in data
        assert 'last_completed' in data
        assert 'status' in data
        assert 'is_overdue' in data
        assert 'days_overdue' in data
        assert 'notification' in data
        
        # Check values
        assert data['status'] == 'PENDING'
        assert data['is_overdue'] is False
        assert data['days_overdue'] == 0
    
    def test_overdue_instance_serialization(self, overdue_instance):
        """Test serializing an overdue notification instance"""
        serializer = NotificationInstanceSerializer(overdue_instance)
        data = serializer.data
        
        # Check overdue-specific values
        assert data['is_overdue'] is True
        assert data['days_overdue'] == 3  # 3 days overdue
    
    def test_completed_instance_serialization(self, completed_instance):
        """Test serializing a completed notification instance"""
        serializer = NotificationInstanceSerializer(completed_instance)
        data = serializer.data
        
        # Check completed-specific values
        assert data['status'] == 'COMPLETED'
        assert data['last_completed'] is not None
        assert data['is_overdue'] is False
        assert data['days_overdue'] == 0
    
    def test_create_instance_serialization(self, water_notification):
        """Test creating a new instance through serializer"""
        data = {
            'notification': water_notification.id,
            'next_due': (timezone.now() + timedelta(days=5)).isoformat(),
            'status': 'PENDING'
        }
        
        serializer = NotificationInstanceSerializer(data=data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        instance = serializer.save()
        assert instance.notification_id == water_notification.id
        assert instance.status == 'PENDING'


@pytest.mark.django_db
class TestNotificationSerializer:
    """Tests for the NotificationSerializer"""
    
    def test_basic_serialization(self, water_notification):
        """Test serializing a basic notification"""
        serializer = NotificationSerializer(water_notification)
        data = serializer.data
        
        # Check all expected fields
        assert 'id' in data
        assert 'garden' in data
        assert 'garden_details' in data
        assert 'name' in data
        assert 'type' in data
        assert 'type_display' in data
        assert 'subtype' in data
        assert 'interval' in data
        assert 'plants' in data
        assert 'created_at' in data
        assert 'upcoming_instance' in data
        
        # Check values
        assert data['name'] == "Water Notification"
        assert data['type'] == NotifTypes.WA
        assert data['type_display'] == "Water"
        assert data['garden'] == water_notification.garden.id
        assert data['garden_details']['name'] == "Test Garden"
    
    def test_serialization_with_plants(self, notification_with_plants):
        """Test serializing a notification with associated plants"""
        serializer = NotificationSerializer(notification_with_plants)
        data = serializer.data
        
        # Check that plants are properly included
        assert len(data['plants']) == 3
        
        # Check that custom_interval is respected
        plant_data = data['plants']
        custom_interval_plant = next(p for p in plant_data if p['plant_details']['common_name'] == "Second Plant")
        assert custom_interval_plant['custom_interval'] == 14
    
    def test_serialization_with_instances(self, notification_with_instances, pending_instance):
        """Test that upcoming instance is included"""
        serializer = NotificationSerializer(notification_with_instances)
        data = serializer.data
        
        # Should include the upcoming pending instance (not completed or overdue)
        assert data['upcoming_instance'] is not None
        assert data['upcoming_instance']['id'] == pending_instance.id
    
    def test_serialization_without_instances(self, water_notification):
        """Test serialization when no instances exist"""
        serializer = NotificationSerializer(water_notification)
        data = serializer.data
        
        assert data['upcoming_instance'] is None
    
    def test_garden_with_no_name(self, user):
        """Test garden_details with unnamed garden"""
        # Create garden with no name
        garden = Garden.objects.create(
            user=user,
            size_x=3,
            size_y=3
        )
        
        notification = Notification.objects.create(
            garden=garden,
            name="Test Notification",
            type=NotifTypes.WA,
            interval=5
        )
        
        serializer = NotificationSerializer(notification)
        data = serializer.data
        
        # Should fallback to "Garden ID"
        assert data['garden_details']['name'] == f"Garden {garden.id}"
    
    def test_create_notification(self, garden, mock_request):
        """Test creating a notification through serializer"""
        data = {
            'garden': garden.id,
            'name': "New Notification",
            'type': NotifTypes.FE,
            'interval': 14
        }
        
        serializer = NotificationSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        notification = serializer.save()
        assert notification.name == "New Notification"
        assert notification.type == NotifTypes.FE
        assert notification.interval == 14
    
    def test_create_other_notification_with_subtype(self, garden, mock_request):
        """Test creating 'Other' notification type with subtype"""
        data = {
            'garden': garden.id,
            'name': "Custom Notification",
            'type': NotifTypes.OT,
            'subtype': "CUSTOM_TYPE",
            'interval': 30
        }
        
        serializer = NotificationSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        notification = serializer.save()
        assert notification.subtype == "CUSTOM_TYPE"
    
    def test_create_other_notification_without_subtype(self, garden, mock_request):
        """Test validation requiring subtype for 'Other' type"""
        data = {
            'garden': garden.id,
            'name': "Invalid Notification",
            'type': NotifTypes.OT,  # Other type
            'interval': 30
            # Missing subtype
        }
        
        serializer = NotificationSerializer(data=data, context={'request': mock_request})
        assert not serializer.is_valid()
        assert 'subtype' in serializer.errors
    
    def test_create_standard_notification_with_subtype(self, garden, mock_request):
        """Test validation rejecting subtype for standard notification types"""
        data = {
            'garden': garden.id,
            'name': "Invalid Notification",
            'type': NotifTypes.WA,  # Water type
            'subtype': "INVALID", # Shouldn't have subtype for standard types
            'interval': 7
        }
        
        serializer = NotificationSerializer(data=data, context={'request': mock_request})
        assert not serializer.is_valid()
        assert 'subtype' in serializer.errors
    
    def test_create_notification_for_other_user_garden(self, other_garden, mock_request):
        """Test validation preventing using another user's garden"""
        data = {
            'garden': other_garden.id,  # Garden belongs to other_user
            'name': "Invalid Notification",
            'type': NotifTypes.WA,
            'interval': 7
        }
        
        serializer = NotificationSerializer(data=data, context={'request': mock_request})
        assert not serializer.is_valid()
        assert 'garden' in serializer.errors


@pytest.mark.django_db
class TestDashboardNotificationSerializer:
    """Tests for the DashboardNotificationSerializer"""
    
    def test_serialization_with_plants_and_instances(self, notification_with_plants, pending_instance):
        """Test full serialization with plants and instances"""
        serializer = DashboardNotificationSerializer(notification_with_plants)
        data = serializer.data
        
        # Check all expected fields
        assert 'id' in data
        assert 'name' in data
        assert 'type' in data
        assert 'type_display' in data
        assert 'subtype' in data
        assert 'garden' in data
        assert 'garden_name' in data
        assert 'plant_names' in data
        assert 'next_due' in data
        assert 'status' in data
        assert 'is_overdue' in data
        assert 'instance_id' in data
        
        # Check values
        assert data['name'] == "Water Notification"
        assert data['type_display'] == "Water"
        assert data['garden_name'] == "Test Garden"
        
        # Should have 3 plants
        assert len(data['plant_names']) == 3
        assert "Test Plant" in data['plant_names']
        assert "Second Plant" in data['plant_names']
        assert "Third Plant" in data['plant_names']
        
        # Should include instance data
        assert data['status'] == 'PENDING'
        assert data['is_overdue'] is False
        assert data['instance_id'] == pending_instance.id
    
    def test_serialization_with_overdue_instance(self, notification_with_plants, overdue_instance, pending_instance):
        """Test that overdue instance is correctly identified"""
        # Delete the pending instance so overdue is first
        pending_instance.delete()
        
        serializer = DashboardNotificationSerializer(notification_with_plants)
        data = serializer.data
        
        assert data['is_overdue'] is True
        assert data['instance_id'] == overdue_instance.id
    
    def test_serialization_without_instances(self, water_notification):
        """Test serialization when no instances exist"""
        serializer = DashboardNotificationSerializer(water_notification)
        data = serializer.data
        
        assert data['next_due'] is None
        assert data['status'] is None
        assert data['is_overdue'] is False
        assert data['instance_id'] is None
    
    def test_serialization_without_plants(self, water_notification):
        """Test plant_names when no plants are associated"""
        serializer = DashboardNotificationSerializer(water_notification)
        data = serializer.data
        
        assert isinstance(data['plant_names'], list)
        assert len(data['plant_names']) == 0
    
    def test_serialization_with_many_plants(self, notification_with_plants, fourth_plant):
        """Test that plant_names handles many plants (should limit to 3)"""
        # Add a fourth plant
        NotificationPlantAssociation.objects.create(
            notification=notification_with_plants,
            plant=fourth_plant
        )
        
        serializer = DashboardNotificationSerializer(notification_with_plants)
        data = serializer.data
        
        # Still should only show 3 plants (limit in the serializer)
        assert len(data['plant_names']) == 3
    
    def test_plant_with_no_common_name(self, water_notification, fourth_plant):
        """Test plant_names handles plants with no common name"""
        # Associate plant with no common name
        NotificationPlantAssociation.objects.create(
            notification=water_notification,
            plant=fourth_plant
        )
        
        serializer = DashboardNotificationSerializer(water_notification)
        data = serializer.data
        
        # Should use scientific name as fallback
        assert "Testus quartus" in data['plant_names']