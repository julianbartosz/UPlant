import pytest
from unittest.mock import patch, Mock, call
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from gardens.models import Garden, GardenLog, PlantHealthStatus
from gardens.signals import (
    garden_saved_handler,
    garden_before_save,
    garden_log_saved_handler,
    garden_log_deleted_handler,
    clear_garden_cache
)

from gardens.tests.factories import (
    GardenFactory,
    GardenLogFactory, 
    HealthyPlantLogFactory,
    UnhealthyPlantLogFactory,
    SmallGardenFactory
)
from plants.tests.factories import APIPlantFactory
from user_management.tests.factories import UserFactory


@pytest.mark.unit
class TestGardenSavedHandler:
    """Tests for the garden_saved_handler signal (post_save)."""
    
    @patch('gardens.signals.create_welcome_notification')
    @patch('gardens.signals.reindex_model')
    def test_garden_creation(self, mock_reindex, mock_welcome, db, settings):
        """Test signal handler creates welcome notification for new gardens."""
        # Enable search indexing for the test
        settings.ENABLE_SEARCH_INDEXING = True
        
        # Create a new garden (triggers signal)
        garden = GardenFactory()
        
        # Check welcome notification was called
        mock_welcome.assert_called_once_with(garden)
        
        # Check reindex was called
        mock_reindex.assert_called_once()
        assert mock_reindex.call_args[0][0] == Garden
        assert garden.id in mock_reindex.call_args[0][1]
    
    @patch('gardens.signals.create_welcome_notification')
    @patch('gardens.signals.reindex_model')
    @patch('gardens.signals.clear_garden_cache')
    def test_garden_update(self, mock_clear_cache, mock_reindex, mock_welcome, db, settings):
        """Test signal handler for garden updates."""
        # Enable search indexing for the test
        settings.ENABLE_SEARCH_INDEXING = True
        
        # Create a garden
        garden = GardenFactory()
        
        # Reset mocks to clear the creation calls
        mock_welcome.reset_mock()
        mock_reindex.reset_mock()
        mock_clear_cache.reset_mock()
        
        # Update the garden (triggers signal again)
        garden.name = "Updated Garden Name"
        garden.save()
        
        # Welcome notification should not be called again
        mock_welcome.assert_not_called()
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(garden)
        
        # Reindex should be called
        mock_reindex.assert_called_once()
    
    @patch('gardens.signals.create_welcome_notification')
    @patch('gardens.signals.reindex_model')
    def test_garden_creation_with_search_disabled(self, mock_reindex, mock_welcome, db, settings):
        """Test garden creation when search indexing is disabled."""
        # Disable search indexing
        settings.ENABLE_SEARCH_INDEXING = False
        
        # Create a new garden (triggers signal)
        garden = GardenFactory()
        
        # Welcome notification should still be called
        mock_welcome.assert_called_once()
        
        # But reindex should not be called
        mock_reindex.assert_not_called()
    
    @patch('gardens.signals.create_welcome_notification')
    def test_garden_creation_welcome_notification_error(self, mock_welcome, db, caplog):
        """Test error handling when welcome notification creation fails."""
        # Make the welcome notification function raise an exception
        mock_welcome.side_effect = Exception("Welcome notification error")
        
        # Create a new garden (triggers signal)
        garden = GardenFactory()
        
        # Welcome notification should have been called
        mock_welcome.assert_called_once()
        
        # The error should be logged
        assert "Failed to create welcome notification" in caplog.text


@pytest.mark.unit
class TestGardenBeforeSave:
    """Tests for the garden_before_save signal (pre_save)."""
    
    @patch('gardens.signals.logger')
    def test_garden_dimension_change(self, mock_logger, db):
        """Test dimension change detection in pre-save signal."""
        # Create a garden
        garden = GardenFactory(size_x=10, size_y=10)
        
        # Change dimensions
        garden.size_x = 8
        garden.size_y = 8
        garden.save()
        
        # Logger should have recorded the change
        mock_logger.info.assert_any_call(
            f"Garden {garden.id} dimensions changed from (10x10) to (8x8)"
        )
    
    @patch('gardens.signals.logger')
    def test_garden_dimension_change_with_out_of_bounds(self, mock_logger, db):
        """Test out-of-bounds plant detection when garden dimensions shrink."""
        # Create a garden with plants
        garden = GardenFactory(size_x=10, size_y=10)
        
        # Add plants near the edge
        GardenLogFactory(garden=garden, x_coordinate=9, y_coordinate=9)
        GardenLogFactory(garden=garden, x_coordinate=8, y_coordinate=9)
        
        # Change dimensions to make plants out of bounds
        garden.size_x = 7
        garden.size_y = 7
        garden.save()
        
        # Logger should have recorded the warning about out-of-bounds plants
        mock_logger.warning.assert_called_with(
            "Garden resize will place 2 plants outside boundaries"
        )
    
    def test_garden_same_dimensions(self, db):
        """Test that no dimension change is detected when dimensions stay the same."""
        # Create a garden
        garden = GardenFactory(size_x=10, size_y=10)
        
        # Update without changing dimensions
        with patch('gardens.signals.logger') as mock_logger:
            garden.name = "New Name"
            garden.save()
            
            # Logger should not have recorded any dimension changes
            for call_args in mock_logger.info.call_args_list:
                assert "dimensions changed" not in str(call_args)


@pytest.mark.unit
class TestGardenLogSavedHandler:
    """Tests for the garden_log_saved_handler signal (post_save)."""
    
    @patch('gardens.signals.create_plant_care_notifications')
    @patch('gardens.signals.reindex_model')
    @patch('gardens.signals.clear_garden_cache')
    def test_new_plant_addition(self, mock_clear_cache, mock_reindex, mock_care_notifs, db, settings):
        """Test signal handler for new plant addition."""
        # Enable search indexing
        settings.ENABLE_SEARCH_INDEXING = True
        
        # Create garden
        garden = GardenFactory()
        plant = APIPlantFactory(common_name="Test Plant")
        
        # Add plant to garden (triggers signal)
        log = GardenLogFactory(garden=garden, plant=plant)
        
        # Care notifications should be created
        mock_care_notifs.assert_called_once_with(log)
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(garden)
        
        # Search index should be updated
        mock_reindex.assert_called_once()
    
    @patch('gardens.signals.handle_health_change')
    @patch('gardens.signals.clear_garden_cache')
    def test_plant_health_change(self, mock_clear_cache, mock_health_change, db):
        """Test signal handler detects plant health status changes."""
        # Create garden log
        log = HealthyPlantLogFactory()
        garden = log.garden
        plant = log.plant
        
        # Change health status
        log.health_status = PlantHealthStatus.POOR
        log.save()
        
        # Health change handler should be called
        mock_health_change.assert_called_once_with(
            PlantHealthStatus.HEALTHY,  # Old status
            PlantHealthStatus.POOR,     # New status
            garden,                     # Garden
            plant                       # Plant
        )
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(garden)
    
    @patch('gardens.signals.logger')
    @patch('gardens.signals.clear_garden_cache')
    def test_plant_moved(self, mock_clear_cache, mock_logger, db):
        """Test signal handler detects plant position changes."""
        # Create garden log
        log = GardenLogFactory(x_coordinate=1, y_coordinate=1)
        garden = log.garden
        
        # Move the plant
        log.x_coordinate = 3
        log.y_coordinate = 4
        log.save()
        
        # Logger should have recorded the move
        mock_logger.info.assert_any_call(
            f"Plant moved from (1, 1) to (3, 4) in garden {garden.id}"
        )
    
    @patch('gardens.signals.handle_plant_care_event')
    @patch('gardens.signals.clear_garden_cache')
    def test_plant_watering_recorded(self, mock_clear_cache, mock_care_event, db):
        """Test signal handler detects watering events."""
        # Create garden log with no recent watering
        log = GardenLogFactory(last_watered=None)
        
        # Record watering
        log.last_watered = timezone.now()
        log.save()
        
        # Care event handler should be called for watering
        mock_care_event.assert_called_once_with(log, 'watering')
    
    @patch('gardens.signals.handle_plant_care_event')
    @patch('gardens.signals.clear_garden_cache')
    def test_plant_fertilizing_recorded(self, mock_clear_cache, mock_care_event, db):
        """Test signal handler detects fertilizing events."""
        # Create garden log with no recent fertilizing
        log = GardenLogFactory(last_fertilized=None)
        
        # Record fertilizing
        log.last_fertilized = timezone.now()
        log.save()
        
        # Care event handler should be called for fertilizing
        mock_care_event.assert_called_once_with(log, 'fertilizing')
    
    @patch('gardens.signals.create_plant_care_notifications')
    def test_new_plant_notification_error(self, mock_care_notifs, db, caplog):
        """Test error handling when care notification creation fails."""
        # Make the care notification function raise an exception
        mock_care_notifs.side_effect = Exception("Care notification error")
        
        # Add plant to garden (triggers signal)
        log = GardenLogFactory()
        
        # Care notifications should have been attempted
        mock_care_notifs.assert_called_once()
        
        # Error should be logged
        assert "Failed to create plant care notifications" in caplog.text
    
    @patch('gardens.signals.handle_health_change')
    def test_health_change_error(self, mock_health_change, db, caplog):
        """Test error handling when health change handler fails."""
        # Make the health change handler raise an exception
        mock_health_change.side_effect = Exception("Health change error")
        
        # Create garden log
        log = HealthyPlantLogFactory()
        
        # Change health status
        log.health_status = PlantHealthStatus.POOR
        log.save()
        
        # Health change handler should have been called
        mock_health_change.assert_called_once()
        
        # Error should be logged
        assert "Failed to handle health change" in caplog.text


@pytest.mark.unit
class TestGardenLogDeletedHandler:
    """Tests for the garden_log_deleted_handler signal (post_delete)."""
    
    @patch('gardens.signals.cleanup_plant_notifications')
    @patch('gardens.signals.clear_garden_cache')
    def test_plant_removal(self, mock_clear_cache, mock_cleanup, db):
        """Test signal handler for plant removal."""
        # Create garden log
        log = GardenLogFactory()
        garden = log.garden
        plant = log.plant
        
        # Delete the log (triggers signal)
        log.delete()
        
        # Notification cleanup should be called
        mock_cleanup.assert_called_once_with(garden, plant)
        
        # Cache should be cleared
        mock_clear_cache.assert_called_once_with(garden)
    
    @patch('gardens.signals.cleanup_plant_notifications')
    def test_plant_removal_notification_error(self, mock_cleanup, db, caplog):
        """Test error handling when notification cleanup fails."""
        # Make the cleanup function raise an exception
        mock_cleanup.side_effect = Exception("Cleanup error")
        
        # Create and delete garden log (triggers signal)
        log = GardenLogFactory()
        log.delete()
        
        # Cleanup should have been attempted
        mock_cleanup.assert_called_once()
        
        # Error should be logged
        assert "Failed to clear plant notifications" in caplog.text
    

@pytest.mark.unit
class TestClearGardenCache:
    """Tests for the clear_garden_cache helper function."""
    
    def test_clear_garden_cache(self, db):
        """Test cache clearing for garden-related cache keys."""
        # Create a garden
        garden = GardenFactory()
        user = garden.user
        
        # Set up some cache entries
        cache.set(f"garden:{garden.id}", "Garden data", 3600)
        cache.set(f"user:{user.id}:gardens", "User's gardens", 3600)
        cache.set(f"user:{user.id}:garden_dashboard", "Dashboard data", 3600)
        
        # Verify cache entries exist
        assert cache.get(f"garden:{garden.id}") == "Garden data"
        assert cache.get(f"user:{user.id}:gardens") == "User's gardens"
        assert cache.get(f"user:{user.id}:garden_dashboard") == "Dashboard data"
        
        # Clear cache
        clear_garden_cache(garden)
        
        # Verify cache entries are cleared
        assert cache.get(f"garden:{garden.id}") is None
        assert cache.get(f"user:{user.id}:gardens") is None
        assert cache.get(f"user:{user.id}:garden_dashboard") is None


@pytest.mark.integration
class TestSignalIntegration:
    """Integration tests for garden signals working together."""
    
    @patch('gardens.signals.create_welcome_notification')
    @patch('gardens.signals.create_plant_care_notifications')
    def test_garden_creation_with_plants(self, mock_plant_care, mock_welcome, db):
        """Test complete flow from garden creation to adding plants."""
        # Create a garden with plants (triggers garden and log signals)
        garden = GardenFactory(with_plants=3)
        
        # Welcome notification should be created once
        mock_welcome.assert_called_once_with(garden)
        
        # Plant care notifications should be created for each plant
        assert mock_plant_care.call_count == 3
    
    @patch('services.notification_service.handle_health_change', create=True)
    @patch('gardens.signals.clear_garden_cache')
    def test_multiple_plant_updates(self, mock_clear_cache, mock_health_change, db):
        """Test handling multiple plant updates in the same garden."""
        # Create garden with multiple plants
        garden = GardenFactory()
        plants = [APIPlantFactory() for _ in range(3)]
        logs = [
            HealthyPlantLogFactory(garden=garden, plant=plant) 
            for plant in plants
        ]
        
        # Reset mock to clear factory calls
        mock_clear_cache.reset_mock()
        
        # Update multiple plants
        for log in logs:
            log.health_status = PlantHealthStatus.FAIR
            log.save()
        
        # Health change handler should be called for each plant
        assert mock_health_change.call_count == 3
        
        # Cache should be cleared once per plant
        assert mock_clear_cache.call_count == 3