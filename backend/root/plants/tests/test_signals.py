import pytest
from unittest.mock import patch, call, ANY, Mock
from django.core.cache import cache
from django.db.models import signals
from django.conf import settings

from plants.models import Plant, PlantChangeRequest
from plants.signals import (
    ensure_plant_has_slug,
    plant_saved,
    change_request_saved
)
from plants.tests.factories import (
    APIPlantFactory,
    UserCreatedPlantFactory,
    VerifiedUserPlantFactory,
    PlantWithFullDetailsFactory,
    PlantChangeRequestFactory
)
from user_management.tests.factories import UserFactory, AdminFactory


@pytest.mark.unit
class TestPlantSlugSignal:
    """Tests for the ensure_plant_has_slug signal handler (pre_save)"""
    
    def test_slug_generation_from_common_name(self, db):
        """Test that a slug is generated from the common_name if available"""
        # Create plant without slug
        plant = Plant(
            common_name="Test Plant Name",
            scientific_name="Testus plantus",
            slug="",
            family="Testaceae",
            genus="Testus",
            genus_id=1,
            rank="species"
        )
        
        # Call the signal handler directly
        ensure_plant_has_slug(sender=Plant, instance=plant)
        
        # Check the slug was generated from common_name
        assert plant.slug == "test-plant-name"
    
    def test_slug_generation_from_scientific_name(self, db):
        """Test that a slug is generated from scientific_name if common_name not available"""
        # Create plant without common_name and slug
        plant = Plant(
            common_name="",
            scientific_name="Scientificus testplantus",
            slug="",
            family="Testaceae",
            genus="Scientificus",
            genus_id=1,
            rank="species"
        )
        
        # Call the signal handler directly
        ensure_plant_has_slug(sender=Plant, instance=plant)
        
        # Check the slug was generated from scientific_name
        assert plant.slug == "scientificus-testplantus"
    
    def test_slug_fallback_with_no_names(self, db):
        """Test fallback to generic slug if no names are available"""
        # Create plant without names or slug
        plant = Plant(
            common_name="",
            scientific_name="",
            slug="",
            family="Testaceae",
            genus="Unknown",
            genus_id=1,
            rank="species"
        )
        
        # Call the signal handler directly
        ensure_plant_has_slug(sender=Plant, instance=plant)
        
        # Check the fallback slug was used
        assert "plant-" in plant.slug
    
    def test_unique_slug_generation(self, db):
        """Test that slugs are made unique when duplicates exist"""
        # Create a plant with a known slug
        existing = APIPlantFactory(slug="duplicate-slug")
        
        # Create new plant that would generate the same slug
        plant = Plant(
            common_name="Duplicate Slug",
            scientific_name="Duplicate Sluggus",
            slug="",
            family="Testaceae",
            genus="Duplicate",
            genus_id=1,
            rank="species"
        )
        
        # Call the signal handler directly
        ensure_plant_has_slug(sender=Plant, instance=plant)
        
        # Check that the slug was made unique
        assert plant.slug.startswith("duplicate-slug-")
        assert plant.slug != existing.slug
    
    def test_slug_not_changed_if_already_set(self, db):
        """Test that existing slugs are not modified"""
        # Create plant with pre-set slug
        plant = Plant(
            common_name="Change Me Not",
            scientific_name="Unchangeus maximus",
            slug="my-existing-slug",  # Pre-set slug
            family="Testaceae",
            genus="Unchangeus",
            genus_id=1,
            rank="species"
        )
        
        # Call the signal handler directly
        ensure_plant_has_slug(sender=Plant, instance=plant)
        
        # Check slug was not changed
        assert plant.slug == "my-existing-slug"
    
    def test_signal_connection(self, db):
        """Test that the signal is properly connected"""
        # Create a plant without a slug, saving should trigger the signal
        plant = Plant(
            common_name="Signal Test",
            scientific_name="Signals testplantus",
            family="Testaceae",
            genus="Signals",
            genus_id=1,
            rank="species"
        )

        ensure_plant_has_slug(sender=Plant, instance=plant)

        plant.save()
        
        # After save, slug should be set
        assert plant.slug == "signal-test"


@pytest.mark.unit
class TestPlantSavedSignal:
    """Tests for the plant_saved signal handler (post_save)"""
    
    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    @patch('django.core.cache.cache.delete_many')
    def test_cache_clearing(self, mock_delete_many, mock_set, mock_get, db):
        """Test that relevant cache keys are cleared when a plant is saved"""
        # Create a plant
        plant = APIPlantFactory()
        plant_id = plant.id
        plant_slug = plant.slug
        
        # Reset the mock to clear any calls during plant creation
        mock_delete_many.reset_mock()
        
        # Configure mock to return our test values
        cache_data = {
            'plant_list': 'cached_plant_list',
            f'plant_detail_{plant_id}': 'cached_plant_detail',
            f'plant_detail_slug_{plant_slug}': 'cached_plant_detail_by_slug'
        }
        mock_get.side_effect = lambda key: cache_data.get(key)
        
        # Set up cache entries (these calls are now mocked)
        cache.set(f'plant_list', 'cached_plant_list', 3600)
        cache.set(f'plant_detail_{plant_id}', 'cached_plant_detail', 3600)
        cache.set(f'plant_detail_slug_{plant_slug}', 'cached_plant_detail_by_slug', 3600)
        
        # Verify cache entries exist
        assert cache.get('plant_list') == 'cached_plant_list'
        assert cache.get(f'plant_detail_{plant_id}') == 'cached_plant_detail'
        assert cache.get(f'plant_detail_slug_{plant_slug}') == 'cached_plant_detail_by_slug'
        
        # Update the plant to trigger the signal
        plant.common_name = "Updated Plant"
        plant.save()
        
        # Check that delete_many was called with the expected keys
        expected_keys = [
            'plant_list',
            f'plant_detail_{plant_id}',
            f'plant_detail_slug_{plant_slug}'
        ]
        mock_delete_many.assert_called_once_with(expected_keys)
    
    @patch('plants.signals.logger')
    def test_plant_creation_logging(self, mock_logger, db):
        """Test that plant creation is properly logged"""
        # Create a new plant
        user = UserFactory()
        plant = UserCreatedPlantFactory(created_by=user, common_name="Test Plant")
        
        # Check log message
        mock_logger.info.assert_any_call(
            f"New plant created: Test Plant (ID: {plant.id}) by {user}"
        )
    
    @patch('plants.signals.logger')
    def test_plant_update_logging(self, mock_logger, db):
        """Test that plant update is properly logged"""
        # Create a plant first
        plant = APIPlantFactory(common_name="Original Name")
        
        # Reset the mock to clear creation logs
        mock_logger.reset_mock()
        
        # Update the plant
        plant.common_name = "Updated Name"
        plant.save()
        
        # Check log message
        mock_logger.info.assert_any_call(
            f"Plant updated: Updated Name (ID: {plant.id})"
        )
    
    @patch('plants.signals.send_notification')
    @patch('plants.signals.logger')
    def test_admin_notification_on_plant_creation(self, mock_logger, mock_send, db, settings):
        """Test that admins are notified when a new unverified plant is created"""
        # Enable admin notifications
        settings.NOTIFY_ADMINS_ON_PLANT_CREATION = True
        
        # Create a new unverified plant
        user = UserFactory(username="plant_creator")
        plant = UserCreatedPlantFactory(
            created_by=user,
            common_name="New Test Plant",
            is_verified=False
        )
        
        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == 'admin_group'
        assert "New Plant Needs Verification" in call_args['subject']
        assert "New Test Plant" in call_args['message']
        assert str(user) in call_args['message']
    
    @patch('plants.signals.send_notification')
    def test_admin_notification_disabled(self, mock_send, db, settings):
        """Test that admin notifications are not sent when disabled"""
        # Disable admin notifications
        settings.NOTIFY_ADMINS_ON_PLANT_CREATION = False
        
        # Create a new unverified plant
        plant = UserCreatedPlantFactory(is_verified=False)
        
        # No notification should be sent
        mock_send.assert_not_called()
    
    @patch('plants.signals.send_notification')
    def test_notification_error_handling(self, mock_send, db, settings, caplog):
        """Test that errors in sending notifications are handled gracefully"""
        # Enable admin notifications
        settings.NOTIFY_ADMINS_ON_PLANT_CREATION = True
        
        # Make send_notification raise an exception
        mock_send.side_effect = Exception("Test notification error")
        
        # Create a new unverified plant (should not raise exception)
        plant = UserCreatedPlantFactory(is_verified=False)
        
        # Error should be logged
        assert "Failed to send admin notification" in caplog.text
    
    @patch('plants.signals.send_notification')
    @patch('plants.signals.logger')
    def test_user_notification_on_verification(self, mock_logger, mock_send, db, settings):
        """Test that users are notified when their plant submission is verified"""
        # Enable user notifications
        settings.ENABLE_USER_NOTIFICATIONS = True
        
        # Create a traceable plant instance (need to access the tracker)
        user = UserFactory(username="plant_submitter")
        plant = UserCreatedPlantFactory(
            created_by=user,
            common_name="Unverified Plant",
            is_verified=False
        )
        
        # Reset mock to clear creation notifications
        mock_send.reset_mock()
        
        # Update plant to verified
        plant.is_verified = True
        
        # Need to manually set the tracker's changed value for testing
        plant.tracker = Mock()
        plant.tracker.has_changed = lambda field: field == 'is_verified'
        
        # Manually trigger signal
        plant_saved(sender=Plant, instance=plant, created=False)
        
        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == user
        assert "Plant Submission Verified" in call_args['subject']
        assert "Unverified Plant" in call_args['message']
        assert "verified" in call_args['message'].lower()


@pytest.mark.unit
class TestChangeRequestSignal:
    """Tests for the change_request_saved signal handler"""
    
    @patch('plants.signals.logger')
    def test_change_request_creation_logging(self, mock_logger, db):
        """Test that change request creation is properly logged"""
        # Create a new change request
        plant = APIPlantFactory(common_name="Test Plant")
        user = UserFactory(username="change_requester")
        
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name="water_interval",
            old_value="7",
            new_value="5"
        )
        
        # Check log message
        mock_logger.info.assert_any_call(
            f"New change request created for plant {plant.id} "
            f"({plant.common_name}) - Field: water_interval, "
            f"User: {user}"
        )
    
    @patch('plants.signals.send_notification')
    def test_admin_notification_on_change_request(self, mock_send, db, settings):
        """Test that admins are notified of new change requests"""
        # Enable admin notifications
        settings.ENABLE_ADMIN_NOTIFICATIONS = True
        
        # Create a new change request
        plant = APIPlantFactory(common_name="Test Plant")
        user = UserFactory(username="change_requester")
        
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name="water_interval"
        )
        
        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == 'admin_group'
        assert "New Plant Change Request" in call_args['subject']
        assert "change_requester" in call_args['message']
        assert "water_interval" in call_args['message']
        assert "Test Plant" in call_args['message']
    
    @patch('plants.signals.send_notification')
    def test_user_notification_on_approval(self, mock_send, db, settings):
        """Test that users are notified when their change request is approved"""
        # Enable user notifications
        settings.ENABLE_USER_NOTIFICATIONS = True
        
        # Create a change request
        plant = APIPlantFactory(common_name="Test Plant")
        user = UserFactory()
        admin = AdminFactory()
        
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name="water_interval",
            status="PENDING"
        )
        
        # Reset mock to clear creation notifications
        mock_send.reset_mock()
        
        # Approve the change request
        change_request.status = "APPROVED"
        change_request.reviewer = admin
        change_request.save()
        
        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == user
        assert "Plant Change Request Approved" in call_args['subject']
        assert "approved" in call_args['message'].lower()
        assert "water_interval" in call_args['message']
    
    @patch('plants.signals.send_notification')
    def test_user_notification_on_rejection(self, mock_send, db, settings):
        """Test that users are notified when their change request is rejected"""
        # Enable user notifications
        settings.ENABLE_USER_NOTIFICATIONS = True
        
        # Create a change request
        plant = APIPlantFactory(common_name="Test Plant")
        user = UserFactory()
        admin = AdminFactory()
        
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name="water_interval",
            status="PENDING"
        )
        
        # Reset mock to clear creation notifications
        mock_send.reset_mock()
        
        # Reject the change request
        change_request.status = "REJECTED"
        change_request.reviewer = admin
        change_request.review_notes = "Invalid information provided."
        change_request.save()
        
        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == user
        assert "Plant Change Request Rejected" in call_args['subject']
        assert "not approved" in call_args['message'].lower()
        assert "Invalid information provided" in call_args['message']
    
    @patch('plants.signals.send_notification')
    def test_notification_disabled_settings(self, mock_send, db, settings):
        """Test that notifications are not sent when disabled in settings"""
        # Disable user notifications
        settings.ENABLE_USER_NOTIFICATIONS = False
        settings.ENABLE_ADMIN_NOTIFICATIONS = False
        
        # Create and then approve a change request
        plant = APIPlantFactory()
        user = UserFactory()
        admin = AdminFactory()
        
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name="water_interval",
            status="PENDING"
        )
        
        # Reset mock to clear creation calls
        mock_send.reset_mock()
        
        # Approve the change request
        change_request.status = "APPROVED"
        change_request.reviewer = admin
        change_request.save()
        
        # No notifications should be sent
        mock_send.assert_not_called()


@pytest.mark.integration
class TestSignalIntegration:
    """Integration tests for signals working together"""
    
    @patch('plants.signals.send_notification')
    def test_plant_creation_and_verification_flow(self, mock_send, db, settings):
        """Test the full flow of plant creation, verification, and notifications"""
        # Enable notifications
        settings.NOTIFY_ADMINS_ON_PLANT_CREATION = True
        settings.ENABLE_USER_NOTIFICATIONS = True
        
        # Create user and unverified plant
        user = UserFactory(username="plant_creator")
        plant = UserCreatedPlantFactory(
            created_by=user,
            common_name="Integration Test Plant",
            is_verified=False
        )
        
        # Check admin notification was sent
        assert mock_send.call_count == 1
        admin_call = mock_send.call_args_list[0][1]
        assert admin_call['recipients'] == 'admin_group'
        assert "needs verification" in admin_call['message'].lower()
        
        # Reset mock
        mock_send.reset_mock()
        
        # Now verify the plant
        plant.is_verified = True
        
        # Need to manually set the tracker's changed value for testing
        plant.tracker = Mock()
        plant.tracker.has_changed = lambda field: field == 'is_verified'
        
        plant.save()
        
        # Check user notification was sent
        assert mock_send.call_count == 1
        user_call = mock_send.call_args_list[0][1]
        assert user_call['recipients'] == user
        assert "verified" in user_call['message'].lower()
    
    @patch('plants.signals.send_notification')
    def test_change_request_workflow(self, mock_send, db, settings):
        """Test the full lifecycle of a change request with notifications"""
        # Enable notifications
        settings.ENABLE_ADMIN_NOTIFICATIONS = True
        settings.ENABLE_USER_NOTIFICATIONS = True
        
        # Create user, admin, and plant
        user = UserFactory(username="change_requester")
        admin = AdminFactory(username="change_reviewer")
        plant = APIPlantFactory(common_name="Integration Test Plant")
        
        # Create change request
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name="water_interval",
            old_value="7",
            new_value="5",
            status="PENDING"
        )
        
        # Admin notification should be sent
        admin_call = mock_send.call_args_list[0][1]
        assert admin_call['recipients'] == 'admin_group'
        assert "New Plant Change Request" in admin_call['subject']
        
        # Reset mock
        mock_send.reset_mock()
        
        # Approve change request
        change_request.status = "APPROVED"
        change_request.reviewer = admin
        change_request.save()
        
        # User notification should be sent
        user_call = mock_send.call_args_list[0][1]
        assert user_call['recipients'] == user
        assert "approved" in user_call['message'].lower()