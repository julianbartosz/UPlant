import pytest
from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.utils import IntegrityError

from notifications.models import Notification, NotificationPlantAssociation, NotificationInstance, NotifTypes
from plants.models import Plant
from gardens.models import Garden, GardenLog

from notifications.tests.factories import (
    NotificationFactory,
    WaterNotificationFactory,
    FertilizeNotificationFactory,
    PruneNotificationFactory,
    HarvestNotificationFactory,
    WeatherNotificationFactory,
    OtherNotificationFactory,
    NotificationPlantAssociationFactory,
    NotificationInstanceFactory,
    OverdueNotificationInstanceFactory,
    CompletedNotificationInstanceFactory,
    SkippedNotificationInstanceFactory,
    MissedNotificationInstanceFactory,
    create_notifications_test_set,
    create_notification_sequence
)
from gardens.tests.factories import GardenFactory, GardenLogFactory
from plants.tests.factories import APIPlantFactory, PlantWithFullDetailsFactory


@pytest.mark.unit
class TestNotificationModel:
    """Test suite for the Notification model."""
    
    def test_notification_creation(self, db):
        """Test creating a notification with valid data."""
        notification = NotificationFactory()
        
        # Check that it was saved to DB with ID
        assert notification.id is not None
        assert notification.name is not None
        assert notification.type in NotifTypes.values
        
        # Verify DB retrieval works
        retrieved_notification = Notification.objects.get(id=notification.id)
        assert retrieved_notification.name == notification.name
    
    def test_notification_string_representation(self, db):
        """Test the string representation of a Notification."""
        notification = NotificationFactory(name="Test Water Notification")
        
        assert str(notification) == f"Notification: {notification.id} - Test Water Notification"
    
    def test_interval_positive_constraint(self, db):
        """Test that interval must be positive."""
        # Try to create a notification with invalid interval
        with pytest.raises(ValidationError):
            notification = NotificationFactory.build(interval=0)
            notification.full_clean()
            
        # Negative interval should also fail
        with pytest.raises(ValidationError):
            notification = NotificationFactory.build(interval=-5)
            notification.full_clean()
            
        # Positive interval should work
        notification = NotificationFactory(interval=1)
        notification.full_clean()  # Should not raise
    
    def test_subtype_validation_for_other_type(self, db):
        """Test that 'Other' type requires subtype but other types don't."""
        # 'Other' type without subtype should fail
        with pytest.raises(ValidationError):
            notification = NotificationFactory(type=NotifTypes.OT, subtype="")
            notification.save()
            
        # 'Other' type with subtype should pass
        notification = OtherNotificationFactory()
        notification.full_clean()  # Should not raise
        
        # Non-other type with subtype should fail
        with pytest.raises(ValidationError):
            notification = WaterNotificationFactory(subtype="Invalid")
            notification.save()
            
        # Non-other type without subtype should pass
        notification = WaterNotificationFactory()
        notification.full_clean()  # Should not raise
    
    def test_type_specific_factories(self, db):
        """Test that each notification type factory creates the correct type."""
        # Test each factory makes correct type
        water = WaterNotificationFactory()
        assert water.type == NotifTypes.WA
        
        fertilize = FertilizeNotificationFactory()
        assert fertilize.type == NotifTypes.FE
        
        prune = PruneNotificationFactory()
        assert prune.type == NotifTypes.PR
        
        harvest = HarvestNotificationFactory()
        assert harvest.type == NotifTypes.HA
        
        weather = WeatherNotificationFactory()
        assert weather.type == NotifTypes.WE
        
        other = OtherNotificationFactory()
        assert other.type == NotifTypes.OT
        assert other.subtype is not None
    
    def test_notification_plants_relationship(self, db):
        """Test the many-to-many relationship with plants."""
        # Create notification with plants
        plants = [APIPlantFactory() for _ in range(3)]
        notification = NotificationFactory()
        
        # Add plants through the association
        for plant in plants:
            NotificationPlantAssociationFactory(notification=notification, plant=plant)
            
        # Check plants were associated
        assert notification.plants.count() == 3
        for plant in plants:
            assert plant in notification.plants.all()
    
    def test_notification_with_plants_factory_hook(self, db):
        """Test the factory post-generation hook for adding plants."""
        # Create notification with 5 plants
        notification = NotificationFactory(plants=5)
        
        # Check plants were created and added
        assert notification.plants.count() == 5
        
        # Create with specific plants
        specific_plants = [APIPlantFactory() for _ in range(2)]
        notification = NotificationFactory(plants=specific_plants)
        
        # Check specific plants were added
        assert notification.plants.count() == 2
        for plant in specific_plants:
            assert plant in notification.plants.all()
    
    def test_notification_garden_cascade_delete(self, db):
        """Test that deleting a garden deletes associated notifications."""
        garden = GardenFactory()
        notification = NotificationFactory(garden=garden)
        notification_id = notification.id
        
        # Delete garden
        garden.delete()
        
        # Notification should be deleted
        assert not Notification.objects.filter(id=notification_id).exists()


@pytest.mark.unit
class TestNotificationPlantAssociation:
    """Test suite for the NotificationPlantAssociation model."""
    
    def test_association_creation(self, db):
        """Test creating a notification-plant association."""
        association = NotificationPlantAssociationFactory()
        
        # Check that it was saved to DB with ID
        assert association.id is not None
        assert association.notification is not None
        assert association.plant is not None
        
        # Custom interval should be None by default (using notification default)
        assert association.custom_interval is None
    
    def test_custom_interval(self, db):
        """Test setting and using a custom interval."""
        notification = NotificationFactory(interval=10)
        association = NotificationPlantAssociationFactory(
            notification=notification,
            custom_interval=5  # Override the default interval
        )
        
        assert association.custom_interval == 5
        assert association.notification.interval == 10  # Default unchanged
    
    def test_unique_constraint(self, db):
        """Test that a plant can only be associated once with a notification."""
        notification = NotificationFactory()
        plant = APIPlantFactory()
        
        # Create first association
        NotificationPlantAssociationFactory(notification=notification, plant=plant)
        
        # Try to create duplicate - should fail with either ValidationError or IntegrityError
        with pytest.raises((ValidationError, IntegrityError)):
            NotificationPlantAssociationFactory(notification=notification, plant=plant)
    
    def test_prevent_duplicate_notification_types(self, db):
        """Test validation preventing duplicate notification types for the same plant in a garden."""
        garden = GardenFactory()
        plant = APIPlantFactory()
        
        # Create first water notification
        notification1 = WaterNotificationFactory(garden=garden)
        association1 = NotificationPlantAssociationFactory(notification=notification1, plant=plant)
        
        # Create second water notification
        notification2 = WaterNotificationFactory(garden=garden)
        
        # Try to associate same plant - should fail validation
        with pytest.raises(ValidationError):
            association2 = NotificationPlantAssociation(
                notification=notification2, 
                plant=plant
            )
            association2.full_clean()
            association2.save()
    
    def test_factory_post_generation_custom_interval(self, db):
        """Test the factory post-generation hook for setting custom intervals."""
        # Test with explicit value
        association = NotificationPlantAssociationFactory(with_custom_interval=7)
        assert association.custom_interval == 7
        
        # Test with True (random interval)
        association = NotificationPlantAssociationFactory(with_custom_interval=True)
        assert association.custom_interval is not None
        assert association.custom_interval > 0


@pytest.mark.unit
class TestNotificationInstance:
    """Test suite for the NotificationInstance model."""
    
    def test_instance_creation(self, db):
        """Test creating a notification instance."""
        instance = NotificationInstanceFactory()
        
        # Check that it was saved to DB with ID
        assert instance.id is not None
        assert instance.notification is not None
        assert instance.next_due is not None
        assert instance.status == 'PENDING'
    
    def test_instance_string_representation(self, db):
        """Test the string representation of a NotificationInstance."""
        now = timezone.now()
        due_date = now + timedelta(days=3)
        instance = NotificationInstanceFactory(
            notification=NotificationFactory(name="Water Plants"),
            next_due=due_date
        )
        
        expected_str = f"Water Plants - Due: {due_date.strftime('%Y-%m-%d')}"
        assert str(instance) == expected_str
    
    def test_is_overdue_property(self, db):
        """Test the is_overdue property."""
        # Past due date - should be overdue
        instance = OverdueNotificationInstanceFactory()
        assert instance.is_overdue is True
        
        # Future due date - should not be overdue
        instance = NotificationInstanceFactory()
        assert instance.is_overdue is False
        
        # No due date - should not be overdue
        instance = NotificationInstanceFactory()
        instance.next_due = None
        assert instance.is_overdue is False
    
    def test_complete_task(self, db):
        """Test the complete_task method."""
        instance = NotificationInstanceFactory()
        
        # Store initial values
        original_status = instance.status
        original_last_completed = instance.last_completed
        original_completed_at = instance.completed_at
        original_next_due = instance.next_due
        
        # Complete the task
        instance.complete_task()
        
        # Check status updated
        assert instance.status == 'COMPLETED'
        assert original_status == 'PENDING'
        
        # Check timestamps
        assert instance.last_completed is not None
        assert instance.completed_at is not None
        assert instance.last_completed > original_last_completed if original_last_completed else instance.last_completed is not None
        assert instance.completed_at > original_completed_at if original_completed_at else instance.completed_at is not None
        
        # Check next_due updated
        expected_next_due = instance.last_completed + timedelta(days=instance.notification.interval)
        assert instance.next_due.date() == expected_next_due.date()
    
    def test_skip_task(self, db):
        """Test the skip_task method."""
        instance = NotificationInstanceFactory()
        
        # Store initial values
        original_status = instance.status
        original_next_due = instance.next_due
        
        # Skip the task
        instance.skip_task()
        
        # Check status updated
        assert instance.status == 'SKIPPED'
        assert original_status == 'PENDING'
        
        # Check next_due updated
        assert instance.next_due > original_next_due
    
    def test_is_harvest_ready_method(self, db):
        """Test the is_harvest_ready method."""
        # Create harvest notification
        garden = GardenFactory()
        notification = HarvestNotificationFactory(garden=garden)
        
        # Create plant with days_to_harvest
        plant = PlantWithFullDetailsFactory(days_to_harvest=Decimal('30.0'))
        
        # Associate plant with notification
        assoc = NotificationPlantAssociationFactory(notification=notification, plant=plant)
        
        # Create notification instance
        instance = NotificationInstanceFactory(notification=notification)
        
        # Initially, with no garden log, plant isn't ready
        assert instance.is_harvest_ready() is False
        
        # Add garden log with plant not yet ready for harvest (just planted)
        log = GardenLogFactory(
            garden=garden,
            plant=plant,
            planted_date=timezone.now().date()  # Today
        )
        
        # Plant still not ready (0 days grown, needs 30)
        assert instance.is_harvest_ready() is False
        
        # Update planted_date to make it ready for harvest
        log.planted_date = timezone.now().date() - timedelta(days=40)  # 40 days ago
        log.save()
        
        # Now plant should be ready for harvest
        assert instance.is_harvest_ready() is True
        
        # Test with non-harvest notification (should always return True)
        water_notif = WaterNotificationFactory(garden=garden)
        water_instance = NotificationInstanceFactory(notification=water_notif)
        assert water_instance.is_harvest_ready() is True
    
    def test_get_active_notifications_class_method(self, db):
        """Test the get_active_notifications class method."""
        # Create notifications in various states using a unique identifier to isolate this test
        unique_name = "UNIQUE_TEST_NAME_9876543210"
        
        # Create a garden and notification with unique name
        garden = GardenFactory()
        notif = NotificationFactory(name=unique_name, garden=garden)
        
        # Create instances in various states
        pending = NotificationInstanceFactory(notification=notif)
        completed = CompletedNotificationInstanceFactory(notification=notif)
        skipped = SkippedNotificationInstanceFactory(notification=notif)
        
        # Get active notifications and filter for only our test notification
        all_active = NotificationInstance.get_active_notifications()
        active = [n for n in all_active if n.notification.name == unique_name]
        
        # Check only pending notifications are returned
        assert pending in active
        assert completed not in active
        assert skipped not in active
        
        # Test with harvest notification for plants that aren't ready
        harvest_notif = HarvestNotificationFactory(garden=garden, name=f"{unique_name}_HARVEST")
        plant = PlantWithFullDetailsFactory(days_to_harvest=Decimal('60.0'))
        NotificationPlantAssociationFactory(notification=harvest_notif, plant=plant)
        
        # Add garden log for a newly planted plant (not ready for harvest)
        GardenLogFactory(
            garden=garden,
            plant=plant,
            planted_date=timezone.now().date()  # Today
        )
        
        harvest_instance = NotificationInstanceFactory(notification=harvest_notif)
        
        # Get active notifications again and filter for our test notifications
        all_active = NotificationInstance.get_active_notifications()
        active = [n for n in all_active if 
                  n.notification.name == unique_name or 
                  n.notification.name == f"{unique_name}_HARVEST"]
        
        # The harvest notification should be excluded since plant isn't ready
        assert harvest_instance not in active
    
    def test_auto_process_old_notifications_class_method(self, db):
        """Test the auto_process_old_notifications class method."""
        # Create old overdue notification
        old_date = timezone.now() - timedelta(days=20)  # 20 days ago
        overdue = NotificationInstanceFactory(next_due=old_date)
        
        # Auto process with 14 day threshold (default)
        result = NotificationInstance.auto_process_old_notifications()
        
        # Check result stats
        assert result['processed'] == 1
        assert result['threshold_days'] == 14
        
        # Check overdue notification was updated
        overdue.refresh_from_db()
        assert overdue.status == 'MISSED'
        assert overdue.next_due > timezone.now()  # Rescheduled for future
        
        # Check new pending notification was created
        new_pending = NotificationInstance.objects.filter(
            notification=overdue.notification,
            status='PENDING'
        ).exclude(id=overdue.id).first()
        
        assert new_pending is not None
        
        # Instead of exact equality, check that the dates are within 1 second of each other
        # This accounts for microsecond differences that occur when timestamps are created
        time_diff = abs((new_pending.next_due - overdue.next_due).total_seconds())
        assert time_diff < 1, f"DateTime difference is {time_diff} seconds, which is more than expected"


@pytest.mark.unit
class TestNotificationIntegration:
    """Test interactions between notification models."""
    
    def test_create_notifications_test_set_factory(self, db):
        """Test the create_notifications_test_set factory helper."""
        test_set = create_notifications_test_set()
        
        # Check all components were created
        assert test_set['user'] is not None
        assert test_set['garden'] is not None
        assert len(test_set['plants']) == 5
        
        # Check all notification types were created
        assert test_set['notifications']['water'] is not None
        assert test_set['notifications']['fertilize'] is not None
        assert test_set['notifications']['prune'] is not None
        assert test_set['notifications']['harvest'] is not None
        assert test_set['notifications']['weather'] is not None
        assert test_set['notifications']['other'] is not None
        
        # Check instances were created
        assert len(test_set['instances']['water']) == 3
        assert len(test_set['instances']['fertilize']) == 2
        
        # Check instance states
        water_instances = test_set['instances']['water']
        assert any(i.status == 'PENDING' for i in water_instances)
        assert any(i.is_overdue for i in water_instances)
        assert any(i.status == 'COMPLETED' for i in water_instances)
        
        # Check plant associations
        water_notif = test_set['notifications']['water']
        assert water_notif.plants.count() == 5
    
    def test_create_notification_sequence_factory(self, db):
        """Test the create_notification_sequence factory helper."""
        notification, instances = create_notification_sequence(
            notification_type=NotifTypes.WA,
            count=10,
            days_span=30
        )
        
        # Check notification created
        assert notification is not None
        assert notification.type == NotifTypes.WA
        
        # Check instances created
        assert len(instances) == 10
        
        # Check instance distribution
        completed_count = sum(1 for i in instances if i.status == 'COMPLETED')
        pending_count = sum(1 for i in instances if i.status == 'PENDING')
        
        # Should be ~70% completed, ~30% pending
        assert completed_count >= 6
        assert pending_count >= 2
        
        # Check notification has associated plants
        assert notification.plants.count() == 2
    
    def test_notification_lifecycle(self, db):
        """Test the full lifecycle of a notification and its instances."""
        # 1. Create garden and plant
        garden = GardenFactory()
        plant = APIPlantFactory(water_interval=3)
        
        # 2. Create water notification
        notification = WaterNotificationFactory(
            garden=garden,
            interval=plant.water_interval
        )
        
        # 3. Associate plant with notification
        assoc = NotificationPlantAssociationFactory(notification=notification, plant=plant)
        
        # 4. Create pending notification instance
        instance = NotificationInstanceFactory(
            notification=notification,
            next_due=timezone.now() - timedelta(hours=1)  # Slightly overdue
        )
        
        # 5. Mark task as completed
        instance.complete_task()
        
        # 6. Verify completed state
        assert instance.status == 'COMPLETED'
        assert instance.last_completed is not None
        assert instance.completed_at is not None
        
        # 7. Verify next due date calculated correctly
        expected_next_due = instance.completed_at + timedelta(days=notification.interval)
        assert abs((instance.next_due - expected_next_due).total_seconds()) < 10  # Within 10 seconds