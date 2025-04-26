import pytest
from unittest.mock import patch, Mock, call
from datetime import timedelta
from django.utils import timezone
from django.db.models import signals
from django.core.cache import cache
from django.test.utils import isolate_apps

from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation, NotifTypes
from notifications.signals import (
    notification_saved_handler,
    notification_deleted_handler,
    instance_saved_handler,
    instance_before_save,
    cleanup_orphaned_notifications,
    process_garden_log_care_activities,
    garden_log_before_save,
    plant_associated_handler,
    plant_disassociated_handler,
    create_first_notification_instance,
    schedule_next_notification,
    clear_notification_cache
)
from notifications.tests.factories import (
    NotificationFactory,
    WaterNotificationFactory,
    FertilizeNotificationFactory,
    NotificationInstanceFactory,
    CompletedNotificationInstanceFactory,
    NotificationPlantAssociationFactory,
    create_notifications_test_set
)
from gardens.tests.factories import GardenFactory, GardenLogFactory
from plants.tests.factories import APIPlantFactory
from user_management.tests.factories import UserFactory


@pytest.mark.unit
class TestNotificationSignals:
    """Tests for notification creation and update signals."""
    
    @patch('notifications.signals.create_first_notification_instance')
    @patch('notifications.signals.clear_notification_cache')
    def test_notification_created(self, mock_clear_cache, mock_create_instance, db):
        """Test that creating a notification triggers an instance creation."""
        # Create notification
        notification = NotificationFactory()
        
        # Check if the first instance was created
        mock_create_instance.assert_called_once_with(notification)
        
        # Check if cache was cleared
        mock_clear_cache.assert_called_once_with(notification)
    
    @patch('notifications.signals.create_first_notification_instance')
    @patch('notifications.signals.clear_notification_cache')
    def test_notification_updated(self, mock_clear_cache, mock_create_instance, db):
        """Test that updating a notification clears the cache but doesn't create new instance."""
        # Create notification
        notification = NotificationFactory()
        
        # Reset mocks to clear creation calls
        mock_create_instance.reset_mock()
        mock_clear_cache.reset_mock()
        
        # Update notification
        notification.name = "Updated Name"
        notification.save()
        
        # First instance should not be created again
        mock_create_instance.assert_not_called()
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(notification)
    
    @patch('notifications.signals.create_first_notification_instance')
    def test_notification_creation_error_handling(self, mock_create_instance, db, caplog):
        """Test error handling during notification creation."""
        # Make the instance creation raise an exception
        mock_create_instance.side_effect = Exception("Test exception")
        
        # Create notification (should not raise the exception)
        notification = NotificationFactory()
        
        # Check if error was logged
        assert "Error creating first notification instance" in caplog.text
    
    @patch('notifications.signals.clear_notification_cache')
    def test_notification_deleted(self, mock_clear_cache, db):
        """Test that deleting a notification clears the cache."""
        # Create notification
        notification = NotificationFactory()
        notification_id = notification.id
        garden = notification.garden
        
        # Delete notification
        notification.delete()
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once()
    
    def test_signal_raw_flag_handling(self, db):
        """Test that the raw flag prevents signal processing for fixtures."""
        with patch('notifications.signals.create_first_notification_instance') as mock:
            # Manually call the signal handler with raw=True
            notification = NotificationFactory.build()
            notification_saved_handler(
                sender=Notification,
                instance=notification,
                created=True,
                raw=True  # Simulating fixture loading
            )
            
            # Signal handler should exit early
            mock.assert_not_called()


@pytest.mark.unit
class TestNotificationInstanceSignals:
    """Tests for notification instance signals."""
    
    @patch('notifications.signals.schedule_next_notification')
    @patch('notifications.signals.clear_notification_cache')
    def test_instance_completed(self, mock_clear_cache, mock_schedule_next, db):
        """Test that completing an instance schedules the next one."""
        # Create instance
        instance = NotificationInstanceFactory()
        notification = instance.notification
        
        # Store previous instance state
        instance._prev_instance = instance
        
        # Complete the instance (triggers signal)
        instance.status = 'COMPLETED'
        instance.save()
        
        # Next instance should be scheduled
        mock_schedule_next.assert_called_once_with(instance)
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(notification)
    
    @patch('notifications.signals.schedule_next_notification')
    @patch('notifications.signals.clear_notification_cache')
    def test_instance_skipped(self, mock_clear_cache, mock_schedule_next, db):
        """Test that skipping an instance schedules the next one."""
        # Create instance
        instance = NotificationInstanceFactory()
        notification = instance.notification
        
        # Store previous instance state
        instance._prev_instance = instance
        
        # Skip the instance (triggers signal)
        instance.status = 'SKIPPED'
        instance.save()
        
        # Next instance should be scheduled
        mock_schedule_next.assert_called_once_with(instance)
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(notification)
    
    @patch('notifications.signals.schedule_next_notification')
    def test_instance_no_status_change(self, mock_schedule_next, db):
        """Test that updating an instance without status change doesn't schedule next."""
        # Create instance
        instance = NotificationInstanceFactory()
        
        # Create previous instance state with same status
        prev_instance = Mock()
        prev_instance.status = instance.status
        instance._prev_instance = prev_instance
        
        # Update message only (triggers signal but without status change)
        instance.message = "Updated message"
        instance.save()
        
        # Next instance should not be scheduled
        mock_schedule_next.assert_not_called()
    
    @patch('notifications.signals.schedule_next_notification')
    def test_instance_status_change_error(self, mock_schedule_next, db, caplog):
        """Test error handling during instance status change."""
        # Create instance
        instance = NotificationInstanceFactory()
        
        # Store previous instance state
        instance._prev_instance = instance
        
        # Make scheduling raise an exception
        mock_schedule_next.side_effect = Exception("Test exception")
        
        # Change status (should not propagate the exception)
        instance.status = 'COMPLETED'
        instance.save()
        
        # Error should be logged
        assert "Error processing notification instance status change" in caplog.text
    
    def test_instance_before_save_handler(self, db):
        """Test the pre_save handler stores previous instance state."""
        # Create instance
        instance = NotificationInstanceFactory()
        original_status = instance.status
        
        # Store a reference to check preservation
        instance_id = instance.id
        
        # Call handler directly
        instance_before_save(sender=NotificationInstance, instance=instance)
        
        # Previous instance should be stored
        assert hasattr(instance, '_prev_instance')
        assert instance._prev_instance.id == instance_id
        assert instance._prev_instance.status == original_status
        
        # Update instance 
        instance.status = 'COMPLETED'
        
        # Original state should be preserved
        assert instance._prev_instance.status == original_status


@pytest.mark.unit
class TestGardenLogSignals:
    """Tests for garden log-related signals."""
    
    @patch('services.notification_service.cleanup_plant_notifications', create=True)
    def test_cleanup_orphaned_notifications(self, mock_cleanup, db):
        """Test that removing the last plant triggers notification cleanup."""
        # Create garden and plant
        garden = GardenFactory()
        plant = APIPlantFactory()
        
        # Add plant to garden
        log = GardenLogFactory(garden=garden, plant=plant)
        
        # Remove plant (triggers signal)
        log.delete()
        
        # Cleanup should be called
        mock_cleanup.assert_called_once_with(garden, plant)
    
    @patch('services.notification_service.cleanup_plant_notifications', create=True)
    def test_not_last_plant_cleanup(self, mock_cleanup, db):
        """Test that removing a plant doesn't trigger cleanup if others remain."""
        # Create garden and plant
        garden = GardenFactory()
        plant = APIPlantFactory()
        
        # Add plant to garden twice in different locations
        log1 = GardenLogFactory(garden=garden, plant=plant, x_coordinate=0, y_coordinate=0)
        log2 = GardenLogFactory(garden=garden, plant=plant, x_coordinate=1, y_coordinate=1)
        
        # Remove one plant (triggers signal)
        log1.delete()
        
        # Cleanup should not be called since another log exists
        mock_cleanup.assert_not_called()
    
    @patch('services.notification_service.cleanup_plant_notifications', create=True)
    def test_cleanup_error_handling(self, mock_cleanup, db, caplog):
        """Test error handling during plant removal cleanup."""
        # Create garden and plant
        garden = GardenFactory()
        plant = APIPlantFactory()
        
        # Add plant to garden
        log = GardenLogFactory(garden=garden, plant=plant)
        
        # Make cleanup raise an exception
        mock_cleanup.side_effect = Exception("Test exception")
        
        # Remove plant (triggers signal)
        log.delete()
        
        # Error should be logged
        assert "Error cleaning up notifications after plant removal" in caplog.text
    
    @patch('services.notification_service.handle_plant_care_event', create=True)
    def test_process_watering_activity(self, mock_handle_care, db):
        """Test that updating last_watered triggers care event."""
        # Create garden log
        log = GardenLogFactory(last_watered=None)
        
        # Store previous log state
        log._prev_log = log
        
        # Update watering time
        log.last_watered = timezone.now()
        log.save()
        
        # Care event should be processed
        mock_handle_care.assert_called_once_with(log, 'watering')
    
    @patch('services.notification_service.handle_plant_care_event', create=True)
    def test_process_fertilizing_activity(self, mock_handle_care, db):
        """Test that updating last_fertilized triggers care event."""
        # Create garden log
        log = GardenLogFactory(last_fertilized=None)
        
        # Store previous log state
        log._prev_log = log
        
        # Update fertilizing time
        log.last_fertilized = timezone.now()
        log.save()
        
        # Care event should be processed
        mock_handle_care.assert_called_once_with(log, 'fertilizing')
    
    @patch('services.notification_service.handle_health_change', create=True)
    def test_process_health_change(self, mock_handle_health, db):
        """Test that health status changes are detected."""
        # Create garden log
        log = GardenLogFactory(health_status='Healthy')
        garden = log.garden
        plant = log.plant
        
        # Store previous log state
        prev_log = Mock()
        prev_log.health_status = 'Healthy'
        prev_log.last_watered = log.last_watered
        prev_log.last_fertilized = log.last_fertilized
        prev_log.last_pruned = log.last_pruned
        log._prev_log = prev_log
        
        # Change health status
        log.health_status = 'Poor'
        log.save()
        
        # Health change should be processed
        mock_handle_health.assert_called_once_with('Healthy', 'Poor', garden, plant)
    
    @patch('services.notification_service.create_plant_care_notifications', create=True)
    def test_new_plant_notifications(self, mock_create_notifications, db):
        """Test that adding a new plant creates care notifications."""
        # Create garden and plant
        garden = GardenFactory()
        plant = APIPlantFactory()
        
        # Add plant to garden (triggers signal)
        log = GardenLogFactory(garden=garden, plant=plant)
        
        # Care notifications should be created
        mock_create_notifications.assert_called_once_with(log)
    
    @patch('services.notification_service.create_plant_care_notifications', create=True)
    def test_new_plant_notifications_error(self, mock_create_notifications, db, caplog):
        """Test error handling during care notification creation."""
        # Make notification creation raise an exception
        mock_create_notifications.side_effect = Exception("Test exception")
        
        # Add plant to garden (should not raise exception)
        GardenLogFactory()
        
        # Error should be logged
        assert "Error creating plant care notifications" in caplog.text
    
    def test_garden_log_before_save_handler(self, db):
        """Test the pre_save handler stores previous log state."""
        # Create garden log
        log = GardenLogFactory(health_status='Healthy')
        
        # Store a reference to check preservation
        log_id = log.id
        original_status = log.health_status
        
        # Call handler directly
        garden_log_before_save(sender=None, instance=log)
        
        # Previous log should be stored
        assert hasattr(log, '_prev_log')
        assert log._prev_log.id == log_id
        assert log._prev_log.health_status == original_status


@pytest.mark.unit
class TestNotificationPlantAssociationSignals:
    """Tests for plant association signals."""
    
    @patch('notifications.signals.clear_notification_cache')
    def test_plant_associated(self, mock_clear_cache, db):
        """Test that adding a plant to a notification clears cache."""
        # Create notification
        notification = NotificationFactory()
        plant = APIPlantFactory()
        
        # Reset mock
        mock_clear_cache.reset_mock()
        
        # Associate plant (triggers signal)
        association = NotificationPlantAssociationFactory(
            notification=notification,
            plant=plant
        )
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(notification)
    
    @patch('notifications.signals.clear_notification_cache')
    def test_plant_disassociated(self, mock_clear_cache, db):
        """Test that removing a plant from a notification clears cache."""
        # Create notification with plant
        notification = NotificationFactory()
        plant = APIPlantFactory()
        association = NotificationPlantAssociationFactory(
            notification=notification,
            plant=plant
        )
        
        # Reset mock
        mock_clear_cache.reset_mock()
        
        # Remove association (triggers signal)
        association.delete()
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(notification)
    
    def test_last_plant_disassociated(self, db):
        """Test that removing the last plant deletes the notification."""
        # Create notification with one plant
        notification = NotificationFactory()
        plant = APIPlantFactory()
        association = NotificationPlantAssociationFactory(
            notification=notification,
            plant=plant
        )
        
        # Store notification ID
        notification_id = notification.id
        
        # Remove association (triggers signal)
        association.delete()
        
        # Notification should be deleted
        assert not Notification.objects.filter(id=notification_id).exists()
    
    def test_plant_disassociation_with_multiple_plants(self, db):
        """Test that removing a plant doesn't delete notification if others remain."""
        # Create notification with two plants
        notification = NotificationFactory()
        plant1 = APIPlantFactory()
        plant2 = APIPlantFactory()
        
        assoc1 = NotificationPlantAssociationFactory(
            notification=notification,
            plant=plant1
        )
        assoc2 = NotificationPlantAssociationFactory(
            notification=notification,
            plant=plant2
        )
        
        # Store notification ID
        notification_id = notification.id
        
        # Remove first association (triggers signal)
        assoc1.delete()
        
        # Notification should not be deleted
        assert Notification.objects.filter(id=notification_id).exists()
    
    @patch('notifications.signals.clear_notification_cache')
    def test_plant_disassociation_error_handling(self, mock_clear_cache, db, caplog):
        """Test error handling during plant disassociation."""
        # Create notification with plant
        notification = NotificationFactory()
        plant = APIPlantFactory()
        association = NotificationPlantAssociationFactory(
            notification=notification,
            plant=plant
        )
        
        # Make clear_cache raise an exception
        mock_clear_cache.side_effect = Exception("Test exception")
        
        # Remove association (should not raise exception)
        association.delete()
        
        # Error should be logged
        assert "Error handling plant disassociation" in caplog.text


@pytest.mark.unit
class TestHelperFunctions:
    """Tests for helper functions in the signals module."""
    
    def test_create_first_notification_instance(self, db):
        """Test creating the first instance for a new notification."""
        # Create notification
        notification = NotificationFactory(interval=7)
        
        # Delete any instances created by the signal
        NotificationInstance.objects.filter(notification=notification).delete()
        
        # Call helper directly
        create_first_notification_instance(notification)
        
        # Check that instance was created
        instance = NotificationInstance.objects.get(notification=notification)
        assert instance.status == 'PENDING'
        
        # Due date should be now + interval
        now = timezone.now()
        expected_due = now + timedelta(days=7)
        # Allow small time difference
        assert abs((instance.next_due - expected_due).total_seconds()) < 10
    
    def test_schedule_next_notification_completed(self, db):
        """Test scheduling the next instance after completing one."""
        # Create notification and instance
        notification = NotificationFactory(interval=7)
        instance = NotificationInstanceFactory(
            notification=notification,
            status='COMPLETED'
        )
        
        # Call helper directly
        schedule_next_notification(instance)
        
        # Check that new instance was created
        instances = NotificationInstance.objects.filter(notification=notification).order_by('id')
        assert instances.count() == 2
        
        # New instance should be pending
        new_instance = instances.last()
        assert new_instance.status == 'PENDING'
        
        # Due date for new instance should be now + interval
        now = timezone.now()
        expected_due = now + timedelta(days=7)
        # Allow small time difference
        assert abs((new_instance.next_due - expected_due).total_seconds()) < 10
    
    def test_schedule_next_notification_skipped(self, db):
        """Test scheduling the next instance after skipping one."""
        # Create notification and skipped instance
        now = timezone.now()
        notification = NotificationFactory(interval=7)
        instance = NotificationInstanceFactory(
            notification=notification,
            status='SKIPPED',
            next_due=now - timedelta(days=1)  # Due yesterday
        )
        
        # Call helper directly
        schedule_next_notification(instance)
        
        # Check that new instance was created
        instances = NotificationInstance.objects.filter(notification=notification).order_by('id')
        assert instances.count() == 2
        
        # New instance should be pending
        new_instance = instances.last()
        assert new_instance.status == 'PENDING'
        
        # Due date for new instance should be old due date + interval
        expected_due = instance.next_due + timedelta(days=7)
        assert new_instance.next_due == expected_due
    
    def test_schedule_next_notification_one_time(self, db):
        """Test that one-time notifications (interval <= 0) don't get rescheduled."""
        # Create one-time notification and instance
        notification = NotificationFactory(interval=0)
        instance = NotificationInstanceFactory(
            notification=notification,
            status='COMPLETED'
        )
        
        # Call helper directly
        schedule_next_notification(instance)
        
        # Check that no new instance was created
        instances = NotificationInstance.objects.filter(notification=notification)
        assert instances.count() == 1
    
    def test_clear_notification_cache(self, db):
        """Test clearing cache entries related to a notification."""
        # Create notification
        notification = NotificationFactory()
        garden = notification.garden
        user = garden.user
        
        # Set cache entries
        cache.set(f"notification:{notification.id}", "test_data", 3600)
        cache.set(f"garden:{garden.id}:notifications", "test_data", 3600)
        cache.set(f"user:{user.id}:notification_dashboard", "test_data", 3600)
        cache.set(f"user:{user.id}:upcoming_notifications", "test_data", 3600)
        cache.set(f"user:{user.id}:garden_dashboard", "test_data", 3600)
        
        # Check cache is set
        assert cache.get(f"notification:{notification.id}") == "test_data"
        
        # Call helper directly
        clear_notification_cache(notification)
        
        # Check all cache entries are cleared
        assert cache.get(f"notification:{notification.id}") is None
        assert cache.get(f"garden:{garden.id}:notifications") is None
        assert cache.get(f"user:{user.id}:notification_dashboard") is None
        assert cache.get(f"user:{user.id}:upcoming_notifications") is None
        assert cache.get(f"user:{user.id}:garden_dashboard") is None
    
    def test_clear_notification_cache_error_handling(self, db, caplog):
        """Test error handling during cache clearing."""
        # Create broken notification
        notification = NotificationFactory()
        
        # Remove garden to cause error
        garden_id = notification.garden.id
        notification.garden = None
        
        # Call helper (should not raise exception)
        clear_notification_cache(notification)
        
        # Error should be logged
        assert "Error clearing notification cache" in caplog.text


@pytest.mark.integration
class TestSignalIntegration:
    """Integration tests for signals working together."""
    
    def test_notification_lifecycle(self, db):
        """Test the complete lifecycle of a notification from creation to completion."""
        # Create notification (signal creates first instance)
        notification = WaterNotificationFactory(interval=7)
        
        # Check that initial instance was created
        instances = NotificationInstance.objects.filter(notification=notification)
        assert instances.count() == 1
        
        # Get the instance
        instance = instances.first()
        assert instance.status == 'PENDING'
        
        # Complete the instance (triggers signals)
        instance.status = 'COMPLETED'
        instance.last_completed = timezone.now()
        instance.completed_at = timezone.now()
        instance.save()
        
        # Check that next instance was scheduled
        instances = NotificationInstance.objects.filter(notification=notification).order_by('id')
        assert instances.count() == 2
        
        # Verify new instance status
        new_instance = instances.last()
        assert new_instance.status == 'PENDING'
        assert new_instance.id != instance.id
    
    def test_plant_care_activity_notification_completion(self, db):
        """Test that recording care activities completes relevant notifications."""
        # Skip import errors by mocking the service function
        with patch('services.notification_service.handle_plant_care_event', create=True) as mock_handle:
            # Create notification set
            notification_set = create_notifications_test_set()
            garden = notification_set['garden']
            plant = notification_set['plants'][0]
            water_notification = notification_set['notifications']['water']
            
            # Get plant log
            log = GardenLogFactory(garden=garden, plant=plant)
            
            # Record watering
            log.last_watered = timezone.now()
            log.save()
            
            # Service function should be called with correct parameters
            mock_handle.assert_called_with(log, 'watering')
    
    def test_garden_log_deletion_notification_cleanup(self, db):
        """Test that deleting a garden log cleans up notifications."""
        # Skip import errors by mocking the service function
        with patch('services.notification_service.cleanup_plant_notifications', create=True) as mock_cleanup:
            # Create notification set
            notification_set = create_notifications_test_set()
            garden = notification_set['garden']
            plant = notification_set['plants'][0]
            
            # Create log for this specific plant
            log = GardenLogFactory(garden=garden, plant=plant)
            
            # Delete log (triggers signal)
            log.delete()
            
            # Cleanup function should be called with garden and plant
            mock_cleanup.assert_called_with(garden, plant)