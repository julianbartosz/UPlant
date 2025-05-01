import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
import logging

from services.notification_service import (
    send_notification,
    create_welcome_notification,
    create_watering_notification,
    create_fertilizing_notification,
    create_pruning_notification,
    create_health_alert,
    create_health_improvement_notification,
    handle_plant_care_event,
    handle_health_change,
    create_plant_care_notifications,
    cleanup_plant_notifications
)

from notifications.models import Notification, NotificationInstance, NotifTypes
from gardens.models import PlantHealthStatus


@pytest.fixture
def garden(db):
    """Create a test garden"""
    from gardens.models import Garden
    from django.contrib.auth import get_user_model
    
    user = get_user_model().objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    garden = Garden.objects.create(
        name="Test Garden",
        description="A garden for testing",
        owner=user
    )
    return garden


@pytest.fixture
def plant(db):
    """Create a test plant"""
    from plants.models import Plant
    
    plant = Plant.objects.create(
        common_name="Test Plant",
        scientific_name="Testus plantus",
        is_verified=True,
        watering_frequency=7,
        fertilizing_frequency=30,
        pruning_frequency=90
    )
    return plant


@pytest.fixture
def user(db):
    """Create a test user"""
    from django.contrib.auth import get_user_model
    
    user = get_user_model().objects.create_user(
        username="garden_owner",
        email="owner@example.com",
        password="password123"
    )
    return user


@pytest.fixture
def garden_plant(db, garden, plant):
    """Create a garden-plant association"""
    from gardens.models import GardenPlant
    
    garden_plant = GardenPlant.objects.create(
        garden=garden,
        plant=plant,
        nickname="Planty",
        health_status=PlantHealthStatus.HEALTHY
    )
    return garden_plant


@pytest.fixture
def garden_log(db, garden, plant):
    """Create a garden log entry"""
    from gardens.models import GardenLog
    
    garden_log = GardenLog.objects.create(
        garden=garden,
        plant=plant,
        log_type="PLANT_ADDED",
        description="Added plant to garden",
    )
    return garden_log


@pytest.mark.django_db
class TestSendNotification:
    """Tests for the send_notification function"""
    
    def test_send_notification_basic(self, garden):
        """Test creating a basic notification"""
        notification = send_notification(
            garden=garden,
            subject="Test Notification",
            message="This is a test notification",
            notification_type="OT"
        )
        
        assert notification is not None
        assert notification.name == "Test Notification"
        assert notification.type == "OT"
        assert notification.subtype == "general"  # Default subtype for OT
        assert notification.interval == 1
        
        # Check the notification instance was created
        instances = NotificationInstance.objects.filter(notification=notification)
        assert instances.count() == 1
        
        instance = instances.first()
        assert instance.message == "This is a test notification"
        assert instance.status == "PENDING"
        
    def test_send_notification_with_plants(self, garden, plant):
        """Test creating a notification with associated plants"""
        notification = send_notification(
            garden=garden,
            subject="Plant Notification",
            message="This notification is about plants",
            notification_type="OT",
            plants=plant
        )
        
        assert notification is not None
        assert notification.plants.count() == 1
        assert notification.plants.first() == plant
        
    def test_send_notification_with_multiple_plants(self, garden, plant):
        """Test creating a notification with multiple plants"""
        from plants.models import Plant
        
        plant2 = Plant.objects.create(
            common_name="Another Plant",
            scientific_name="Testus secundus"
        )
        
        notification = send_notification(
            garden=garden,
            subject="Multiple Plants",
            message="This notification is about multiple plants",
            notification_type="OT",
            plants=[plant, plant2]
        )
        
        assert notification is not None
        assert notification.plants.count() == 2
        
    def test_send_notification_invalid_type(self, garden):
        """Test handling invalid notification type"""
        notification = send_notification(
            garden=garden,
            subject="Invalid Type",
            message="Testing invalid notification type",
            notification_type="XX"  # Invalid type code
        )
        
        assert notification is not None
        assert notification.type == "OT"  # Should fall back to OT
        
    def test_send_notification_with_link(self, garden):
        """Test creating a notification with a link"""
        notification = send_notification(
            garden=garden,
            subject="Link Notification",
            message="This notification has a link",
            notification_type="OT",
            link="https://example.com"
        )
        
        assert notification is not None
        
        instance = NotificationInstance.objects.filter(notification=notification).first()
        assert instance is not None
        assert "https://example.com" in instance.message
        
    def test_send_notification_without_garden(self, user):
        """Test notification creation fails without a garden"""
        notification = send_notification(
            recipients=user,
            subject="No Garden",
            message="This shouldn't work without a garden"
        )
        
        assert notification is None
        
    def test_send_notification_with_recipient_garden(self, user, garden):
        """Test creating a notification using recipient's garden"""
        from gardens.models import Garden
        
        # Link the user to the garden
        garden.owner = user
        garden.save()
        
        # Mock the relationship between user and gardens
        with patch.object(user, 'gardens') as mock_gardens:
            mock_queryset = MagicMock()
            mock_queryset.first.return_value = garden
            mock_gardens.return_value = mock_queryset
            
            notification = send_notification(
                recipients=user,
                subject="User Garden",
                message="Using user's garden"
            )
            
            assert notification is not None
            assert notification.garden == garden
            
    def test_send_notification_with_due_date(self, garden):
        """Test creating a notification with a specific due date"""
        future_date = timezone.now() + timedelta(days=7)
        
        notification = send_notification(
            garden=garden,
            subject="Future Notification",
            message="This is due in the future",
            notification_type="OT",
            due_date=future_date
        )
        
        assert notification is not None
        
        instance = NotificationInstance.objects.filter(notification=notification).first()
        assert instance is not None
        
        # Compare the dates, ignoring milliseconds
        assert instance.next_due.strftime('%Y-%m-%d %H:%M:%S') == future_date.strftime('%Y-%m-%d %H:%M:%S')
        
    def test_send_notification_with_error(self, garden):
        """Test error handling in notification creation"""
        # Mock Notification.objects.create to raise an exception
        with patch('notifications.models.Notification.objects.create', side_effect=Exception("Test error")):
            # Should return None and not crash
            notification = send_notification(
                garden=garden,
                subject="Error Test",
                message="This should handle errors"
            )
            
            assert notification is None


@pytest.mark.django_db
class TestHelperFunctions:
    """Tests for notification helper functions"""
    
    def test_create_welcome_notification(self, garden):
        """Test creating a welcome notification"""
        notification = create_welcome_notification(garden)
        
        assert notification is not None
        assert notification.name == "Welcome to your new garden!"
        assert notification.type == "OT"
        assert notification.subtype == "welcome"
        
        instance = NotificationInstance.objects.filter(notification=notification).first()
        assert "Test Garden" in instance.message  # Should include garden name
        
    def test_create_watering_notification(self, garden, plant):
        """Test creating a watering notification"""
        notification = create_watering_notification(garden, plant)
        
        assert notification is not None
        assert notification.name == "Water Test Plant"
        assert notification.type == "WA"
        assert notification.interval == 7  # Default interval
        assert notification.plants.first() == plant
        
        instance = NotificationInstance.objects.filter(notification=notification).first()
        # Due date should be 7 days from now
        assert (instance.next_due - timezone.now()).days >= 6
        
    def test_create_fertilizing_notification(self, garden, plant):
        """Test creating a fertilizing notification"""
        notification = create_fertilizing_notification(garden, plant)
        
        assert notification is not None
        assert notification.name == "Fertilize Test Plant"
        assert notification.type == "FE"
        assert notification.interval == 30  # Default interval
        assert notification.plants.first() == plant
        
        instance = NotificationInstance.objects.filter(notification=notification).first()
        # Due date should be 30 days from now
        assert (instance.next_due - timezone.now()).days >= 29
        
    def test_create_pruning_notification(self, garden, plant):
        """Test creating a pruning notification"""
        notification = create_pruning_notification(garden, plant)
        
        assert notification is not None
        assert notification.name == "Prune Test Plant"
        assert notification.type == "PR"
        assert notification.interval == 90  # Default interval
        assert notification.plants.first() == plant
        
    def test_create_health_alert(self, garden, plant):
        """Test creating a health alert notification"""
        notification = create_health_alert(garden, plant)
        
        assert notification is not None
        assert notification.name == "Test Plant needs attention"
        assert notification.type == "OT"
        assert notification.subtype == "health-alert"
        assert notification.plants.first() == plant
        
    def test_create_health_improvement_notification(self, garden, plant):
        """Test creating a health improvement notification"""
        notification = create_health_improvement_notification(garden, plant)
        
        assert notification is not None
        assert notification.name == "Plant health improved"
        assert notification.type == "OT"
        assert notification.subtype == "health-improvement"
        assert notification.plants.first() == plant


@pytest.mark.django_db
class TestHandlePlantCareEvent:
    """Tests for handle_plant_care_event function"""
    
    def setup_pending_notifications(self, garden, plant):
        """Helper to create pending notifications for a plant"""
        # Create watering notification
        water_notif = Notification.objects.create(
            garden=garden,
            name="Water Test Plant",
            type="WA",
            interval=7
        )
        water_notif.plants.add(plant)
        NotificationInstance.objects.create(
            notification=water_notif,
            status="PENDING",
            next_due=timezone.now(),
            message="Water your plant"
        )
        
        # Create fertilizing notification
        fert_notif = Notification.objects.create(
            garden=garden,
            name="Fertilize Test Plant",
            type="FE",
            interval=30
        )
        fert_notif.plants.add(plant)
        NotificationInstance.objects.create(
            notification=fert_notif,
            status="PENDING",
            next_due=timezone.now(),
            message="Fertilize your plant"
        )
        
        return water_notif, fert_notif
    
    def test_handle_watering_event(self, garden, plant, garden_log):
        """Test handling a watering event"""
        water_notif, _ = self.setup_pending_notifications(garden, plant)
        
        handle_plant_care_event(garden_log, "watering")
        
        # The watering notification should be marked completed
        instance = NotificationInstance.objects.get(notification=water_notif)
        assert instance.status == "COMPLETED"
        assert instance.completed_at is not None
        
    def test_handle_fertilizing_event(self, garden, plant, garden_log):
        """Test handling a fertilizing event"""
        _, fert_notif = self.setup_pending_notifications(garden, plant)
        
        handle_plant_care_event(garden_log, "fertilizing")
        
        # The fertilizing notification should be marked completed
        instance = NotificationInstance.objects.get(notification=fert_notif)
        assert instance.status == "COMPLETED"
        assert instance.completed_at is not None
        
    def test_handle_unknown_care_type(self, garden, plant, garden_log):
        """Test handling an unknown care type"""
        water_notif, fert_notif = self.setup_pending_notifications(garden, plant)
        
        # This should do nothing
        handle_plant_care_event(garden_log, "unknown_type")
        
        # No notifications should be completed
        water_instance = NotificationInstance.objects.get(notification=water_notif)
        fert_instance = NotificationInstance.objects.get(notification=fert_notif)
        
        assert water_instance.status == "PENDING"
        assert fert_instance.status == "PENDING"
        
    def test_handle_multiple_pending_instances(self, garden, plant, garden_log):
        """Test handling multiple pending notification instances"""
        water_notif = Notification.objects.create(
            garden=garden,
            name="Water Test Plant",
            type="WA",
            interval=7
        )
        water_notif.plants.add(plant)
        
        # Create multiple pending instances
        for i in range(3):
            NotificationInstance.objects.create(
                notification=water_notif,
                status="PENDING",
                next_due=timezone.now() + timedelta(days=i),
                message=f"Water your plant ({i+1})"
            )
            
        handle_plant_care_event(garden_log, "watering")
        
        # All instances should be marked as completed
        instances = NotificationInstance.objects.filter(notification=water_notif)
        assert instances.count() == 3
        for instance in instances:
            assert instance.status == "COMPLETED"
            assert instance.completed_at is not None


@pytest.mark.django_db
class TestHandleHealthChange:
    """Tests for handle_health_change function"""
    
    def test_health_decline_to_poor(self, garden, plant):
        """Test handling a health decline to poor status"""
        handle_health_change(PlantHealthStatus.HEALTHY, PlantHealthStatus.POOR, garden, plant)
        
        # Should create a health alert notification
        notifications = Notification.objects.filter(
            garden=garden,
            type="OT",
            subtype="health-alert"
        )
        
        assert notifications.count() == 1
        notification = notifications.first()
        assert notification.plants.first() == plant
        
    def test_health_decline_no_duplicate(self, garden, plant):
        """Test that health alerts are not duplicated"""
        # Create an existing health alert
        notif = Notification.objects.create(
            garden=garden,
            name="Test Plant needs attention",
            type="OT",
            subtype="health-alert",
            interval=1
        )
        notif.plants.add(plant)
        
        # This should not create another alert
        handle_health_change(PlantHealthStatus.HEALTHY, PlantHealthStatus.POOR, garden, plant)
        
        # Should still only have one notification
        notifications = Notification.objects.filter(
            garden=garden,
            type="OT",
            subtype="health-alert"
        )
        
        assert notifications.count() == 1
        
    def test_health_improvement_from_poor(self, garden, plant):
        """Test handling a health improvement from poor to healthy"""
        handle_health_change(PlantHealthStatus.POOR, PlantHealthStatus.HEALTHY, garden, plant)
        
        # Should create a health improvement notification
        notifications = Notification.objects.filter(
            garden=garden,
            type="OT",
            subtype="health-improvement"
        )
        
        assert notifications.count() == 1
        notification = notifications.first()
        assert notification.plants.first() == plant
        
    def test_health_improvement_from_dying(self, garden, plant):
        """Test handling a health improvement from dying to excellent"""
        handle_health_change(PlantHealthStatus.DYING, PlantHealthStatus.EXCELLENT, garden, plant)
        
        # Should create a health improvement notification
        notifications = Notification.objects.filter(
            garden=garden,
            type="OT",
            subtype="health-improvement"
        )
        
        assert notifications.count() == 1
        
    def test_no_notification_for_minor_changes(self, garden, plant):
        """Test that minor health changes don't create notifications"""
        # Good to Excellent is not a significant improvement
        handle_health_change(PlantHealthStatus.GOOD, PlantHealthStatus.EXCELLENT, garden, plant)
        
        # Should not create any notifications
        notifications = Notification.objects.filter(
            garden=garden,
            type="OT",
            subtype__in=["health-alert", "health-improvement"]
        )
        
        assert notifications.count() == 0


@pytest.mark.django_db
class TestCreatePlantCareNotifications:
    """Tests for create_plant_care_notifications function"""
    
    def test_create_all_care_notifications(self, garden_log):
        """Test creating all care notifications for a plant"""
        create_plant_care_notifications(garden_log)
        
        # Should create water, fertilize, and prune notifications
        water_notifs = Notification.objects.filter(garden=garden_log.garden, type="WA")
        fert_notifs = Notification.objects.filter(garden=garden_log.garden, type="FE")
        prune_notifs = Notification.objects.filter(garden=garden_log.garden, type="PR")
        
        assert water_notifs.count() == 1
        assert fert_notifs.count() == 1
        assert prune_notifs.count() == 1
        
        # Check that intervals match the plant's attributes
        assert water_notifs.first().interval == garden_log.plant.watering_frequency
        assert fert_notifs.first().interval == garden_log.plant.fertilizing_frequency
        assert prune_notifs.first().interval == garden_log.plant.pruning_frequency
        
    def test_create_notifications_missing_frequencies(self, garden_log):
        """Test handling missing frequency attributes"""
        # Remove frequency values
        plant = garden_log.plant
        plant.watering_frequency = None
        plant.fertilizing_frequency = None
        plant.pruning_frequency = None
        plant.save()
        
        create_plant_care_notifications(garden_log)
        
        # No notifications should be created
        notifs = Notification.objects.filter(garden=garden_log.garden)
        assert notifs.count() == 0
        
    def test_create_notifications_zero_frequencies(self, garden_log):
        """Test handling zero frequency values"""
        # Set frequencies to zero
        plant = garden_log.plant
        plant.watering_frequency = 0
        plant.fertilizing_frequency = 0
        plant.pruning_frequency = 0
        plant.save()
        
        create_plant_care_notifications(garden_log)
        
        # No notifications should be created
        notifs = Notification.objects.filter(garden=garden_log.garden)
        assert notifs.count() == 0
        
    def test_missing_plant(self, garden_log):
        """Test handling a garden log with no plant"""
        garden_log.plant = None
        garden_log.save()
        
        # Should not create any notifications but also not crash
        create_plant_care_notifications(garden_log)
        
        notifs = Notification.objects.filter(garden=garden_log.garden)
        assert notifs.count() == 0


@pytest.mark.django_db
class TestCleanupPlantNotifications:
    """Tests for cleanup_plant_notifications function"""
    
    def setup_notifications(self, garden, plant):
        """Helper to create notifications for testing cleanup"""
        # Create a notification with only this plant
        single_plant_notif = Notification.objects.create(
            garden=garden,
            name="Single Plant Notification",
            type="WA",
            interval=7
        )
        single_plant_notif.plants.add(plant)
        
        # Create another plant
        from plants.models import Plant
        other_plant = Plant.objects.create(
            common_name="Other Plant",
            scientific_name="Otheria plantus"
        )
        
        # Create a notification with multiple plants
        multi_plant_notif = Notification.objects.create(
            garden=garden,
            name="Multi Plant Notification",
            type="OT",
            interval=1
        )
        multi_plant_notif.plants.add(plant)
        multi_plant_notif.plants.add(other_plant)
        
        return single_plant_notif, multi_plant_notif, other_plant
    
    def test_cleanup_single_plant_notification(self, garden, plant):
        """Test cleaning up a notification with a single plant"""
        single_plant_notif, _, _ = self.setup_notifications(garden, plant)
        
        cleanup_plant_notifications(garden, plant)
        
        # The single-plant notification should be deleted
        assert not Notification.objects.filter(id=single_plant_notif.id).exists()
        
    def test_cleanup_multi_plant_notification(self, garden, plant):
        """Test cleaning up a notification with multiple plants"""
        _, multi_plant_notif, other_plant = self.setup_notifications(garden, plant)
        
        cleanup_plant_notifications(garden, plant)
        
        # The multi-plant notification should still exist
        assert Notification.objects.filter(id=multi_plant_notif.id).exists()
        
        # But it should no longer have the removed plant
        updated_notif = Notification.objects.get(id=multi_plant_notif.id)
        assert plant not in updated_notif.plants.all()
        assert other_plant in updated_notif.plants.all()
        
    def test_cleanup_all_notifications(self, garden, plant):
        """Test cleaning up all of a plant's notifications"""
        single_plant_notif, multi_plant_notif, _ = self.setup_notifications(garden, plant)
        
        cleanup_plant_notifications(garden, plant)
        
        # Single-plant notification should be deleted
        assert not Notification.objects.filter(id=single_plant_notif.id).exists()
        
        # Multi-plant notification should be updated
        updated_notif = Notification.objects.get(id=multi_plant_notif.id)
        assert plant not in updated_notif.plants.all()
        
    def test_cleanup_with_null_plant(self, garden):
        """Test cleanup with a null plant"""
        # Should not raise an exception
        cleanup_plant_notifications(garden, None)