import pytest
import json
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.text import slugify
from decimal import Decimal

from plants.models import Plant, PlantChangeRequest
from plants.tests.factories import (
    APIPlantFactory, 
    UserCreatedPlantFactory,
    VerifiedUserPlantFactory,
    PlantWithFullDetailsFactory,
    PlantChangeRequestFactory
)
from user_management.tests.factories import UserFactory, AdminFactory, ModeratorFactory

@pytest.mark.unit
class TestPlantBasicModel:
    """Test basic functionality of the Plant model."""
    
    def test_plant_creation(self, db):
        """Test creating a plant with valid data."""
        plant = APIPlantFactory()
        
        # Check that it was saved to DB with ID
        assert plant.id is not None
        assert plant.scientific_name is not None
        assert plant.slug is not None
        
        # Verify DB retrieval works
        retrieved_plant = Plant.objects.get(id=plant.id)
        assert retrieved_plant.scientific_name == plant.scientific_name
    
    def test_plant_string_representation(self, db):
        """Test the string representation of a Plant."""
        plant = APIPlantFactory(
            scientific_name="Testus plantus",
            slug="testus-plantus"
        )
        
        assert str(plant) == "Testus plantus (testus-plantus)"
    
    def test_plant_required_fields(self, db):
        """Test that required fields are validated."""
        # Try to create a plant with missing required fields
        with pytest.raises(ValidationError):
            plant = Plant(
                # Missing scientific_name
                slug="test-plant",
                family="Test Family",
                genus="Test",
                genus_id=1,
                rank="species"
            )
            plant.full_clean()
    
    def test_user_created_plant_required_fields(self, db):
        """Test that user-created plants require specific fields."""
        user = UserFactory()
        
        # Missing water_interval (required for user plants)
        with pytest.raises(ValidationError):
            Plant.create_user_plant(
                user=user,
                common_name="My Plant"
                # Missing water_interval
            )
        
        # Missing common_name (required for user plants)
        with pytest.raises(ValidationError):
            Plant.create_user_plant(
                user=user,
                water_interval=7
                # Missing common_name
            )
            
        # With all required fields - should work
        plant = Plant.create_user_plant(
            user=user,
            common_name="Valid Plant",
            water_interval=7
        )
        
        assert plant.id is not None
        assert plant.is_user_created is True
        assert plant.common_name == "Valid Plant"
        assert plant.water_interval == 7

    def test_indexes_exist(self, db):
        """Test that important indexes are defined."""
        # This test verifies the database has the defined indexes
        # Uses Django's introspection API
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check for common_name index
            cursor.execute(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_plant_common_name'"
            )
            assert cursor.fetchone() is not None, "Common name index not found"
            
            # Check for created_by index
            cursor.execute(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_plant_created_by'"
            )
            assert cursor.fetchone() is not None, "Created by index not found"


@pytest.mark.unit
class TestPlantJsonFields:
    """Test JSON field handling in the Plant model."""
    
    def test_json_field_loading(self, db):
        """Test that JSON fields load and store properly."""
        test_data = {
            'synonyms': ["Synonym A", "Synonym B", "Synonym C"],
            'duration': ["perennial", "annual"],
            'edible_part': ["fruit", "leaves", "roots"],
            'flower_color': ["red", "yellow"],
            'foliage_color': ["green", "variegated"],
            'fruit_or_seed_color': ["orange", "red"],
            'growth_months': ["apr", "may", "jun", "jul"],
            'bloom_months': ["jun", "jul"],
            'fruit_months': ["aug", "sep"]
        }
        
        plant = APIPlantFactory(**test_data)
        
        # Get fresh instance from DB
        plant = Plant.objects.get(id=plant.id)
        
        # Check all JSON fields match
        for field, value in test_data.items():
            stored_value = getattr(plant, field)
            assert stored_value == value, f"JSON field {field} doesn't match expected value"
    
    def test_empty_json_fields(self, db):
        """Test empty JSON field handling."""
        # Test with empty lists
        plant = APIPlantFactory(
            synonyms=[],
            duration=[],
            edible_part=None  # Test with null
        )
        
        # Get fresh instance from DB
        plant = Plant.objects.get(id=plant.id)
        
        assert plant.synonyms == []
        assert plant.duration == []
        assert plant.edible_part is None


@pytest.mark.unit
class TestPlantConstraints:
    """Test database constraints in the Plant model."""
    
    def test_water_interval_positive_constraint(self, db):
        """Test water_interval must be positive."""
        with pytest.raises(ValidationError):
            plant = APIPlantFactory(water_interval=0)
            plant.full_clean()
    
    def test_days_to_harvest_positive_constraint(self, db):
        """Test days_to_harvest must be non-negative if provided."""
        # Negative value - should fail
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(days_to_harvest=Decimal('-1.0'))
            plant.full_clean()
            
        # Zero value - should pass
        plant = PlantWithFullDetailsFactory(days_to_harvest=Decimal('0.0'))
        plant.full_clean()  # Should not raise
        
        # Null value - should pass
        plant = PlantWithFullDetailsFactory(days_to_harvest=None)
        plant.full_clean()  # Should not raise
    
    def test_ph_range_constraints(self, db):
        """Test pH values are within valid range (0-14)."""
        # Invalid pH maximum (too high)
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(ph_maximum=Decimal('15.0'))
            plant.full_clean()
            
        # Invalid pH minimum (negative)
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(ph_minimum=Decimal('-1.0'))
            plant.full_clean()
            
        # Invalid range (min > max)
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(
                ph_minimum=Decimal('8.0'),
                ph_maximum=Decimal('7.0')
            )
            plant.full_clean()
            
        # Valid range
        plant = PlantWithFullDetailsFactory(
            ph_minimum=Decimal('6.5'),
            ph_maximum=Decimal('7.5')
        )
        plant.full_clean()  # Should not raise
    
    def test_temperature_range_constraint(self, db):
        """Test min_temperature <= max_temperature."""
        # Invalid range (min > max)
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(
                min_temperature=30,
                max_temperature=20
            )
            plant.full_clean()
            
        # Valid range
        plant = PlantWithFullDetailsFactory(
            min_temperature=5,
            max_temperature=30
        )
        plant.full_clean()  # Should not raise
        
        # One value null is allowed
        plant = PlantWithFullDetailsFactory(
            min_temperature=5,
            max_temperature=None
        )
        plant.full_clean()  # Should not raise
        
        plant = PlantWithFullDetailsFactory(
            min_temperature=None,
            max_temperature=30
        )
        plant.full_clean()  # Should not raise
    
    def test_precipitation_constraints(self, db):
        """Test precipitation values are valid."""
        # Negative minimum precipitation
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(minimum_precipitation=-100)
            plant.full_clean()
            
        # Max < Min precipitation
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(
                minimum_precipitation=1000,
                maximum_precipitation=500
            )
            plant.full_clean()
            
        # Valid values
        plant = PlantWithFullDetailsFactory(
            minimum_precipitation=500,
            maximum_precipitation=1000
        )
        plant.full_clean()  # Should not raise
    
    def test_dimension_constraints(self, db):
        """Test dimensional values are positive."""
        # Negative row spacing
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(row_spacing_cm=Decimal('-10.0'))
            plant.full_clean()
            
        # Negative spread
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(spread_cm=Decimal('-10.0'))
            plant.full_clean()
            
        # Negative root depth
        with pytest.raises(ValidationError):
            plant = PlantWithFullDetailsFactory(minimum_root_depth=-10)
            plant.full_clean()
            
        # Valid values
        plant = PlantWithFullDetailsFactory(
            row_spacing_cm=Decimal('30.0'),
            spread_cm=Decimal('50.0'),
            minimum_root_depth=20
        )
        plant.full_clean()  # Should not raise


@pytest.mark.unit
class TestPlantPermissions:
    """Test permission handling in the Plant model."""
    
    def test_can_user_edit_field(self, db):
        """Test the can_user_edit_field method."""
        plant = APIPlantFactory()
        admin = AdminFactory()
        mod = ModeratorFactory()
        user = UserFactory()
        
        # Admin can edit any field
        assert plant.can_user_edit_field(admin, "scientific_name") is True  # Admin-only field
        assert plant.can_user_edit_field(admin, "common_name") is True  # User-editable field
        
        # Moderators should have staff permission
        assert plant.can_user_edit_field(mod, "scientific_name") is True  # Admin-only field
        
        # Regular user can only edit user-editable fields
        assert plant.can_user_edit_field(user, "common_name") is True  # User-editable field
        assert plant.can_user_edit_field(user, "scientific_name") is False  # Admin-only field
    
    def test_user_editable_fields_constant(self):
        """Test the USER_EDITABLE_FIELDS constant contains expected fields."""
        expected_fields = [
            'common_name', 'image_url', 'water_interval', 'fertilizing_interval', 
            'pruning_interval', 'sunlight_requirements', 'soil_type', 'min_temperature', 
            'max_temperature', 'detailed_description', 'care_instructions', 
            'nutrient_requirements', 'maintenance_notes'
        ]
        
        for field in expected_fields:
            assert field in Plant.USER_EDITABLE_FIELDS
    
    def test_admin_only_fields_constant(self):
        """Test the ADMIN_ONLY_FIELDS constant contains expected fields."""
        expected_admin_fields = [
            'api_id', 'slug', 'scientific_name', 'family', 'genus_id', 'genus'
        ]
        
        for field in expected_admin_fields:
            assert field in Plant.ADMIN_ONLY_FIELDS


@pytest.mark.unit
class TestPlantFactoryMethods:
    """Test factory methods for creating plants."""
    
    def test_create_user_plant(self, db):
        """Test the create_user_plant factory method."""
        user = UserFactory()
        
        plant = Plant.create_user_plant(
            user=user,
            common_name="My Test Plant",
            water_interval=5,
            sunlight_requirements="Partial Shade",
            soil_type="Well-draining"
        )
        
        # Check standard fields
        assert plant.id is not None
        assert plant.common_name == "My Test Plant"
        assert plant.water_interval == 5
        assert plant.sunlight_requirements == "Partial Shade"
        assert plant.soil_type == "Well-draining"
        
        # Check metadata
        assert plant.is_user_created is True
        assert plant.created_by == user
        assert plant.is_verified is False
        
        # Check auto-generated fields
        assert plant.scientific_name == "User Plant: My Test Plant"
        assert "my-test-plant" in plant.slug
        assert plant.family == "User Plants"
        assert plant.genus == "User"
        assert plant.rank == "species"
        assert plant.genus_id > 1000000  # Should use a high ID
    
    def test_create_user_plant_with_scientific_name(self, db):
        """Test create_user_plant with provided scientific name."""
        user = UserFactory()
        
        plant = Plant.create_user_plant(
            user=user,
            common_name="Rose",
            water_interval=3,
            scientific_name="Rosa something"
        )
        
        assert plant.scientific_name == "Rosa something"
        assert plant.genus == "Rosa"  # Should extract genus from scientific name
    
    def test_create_user_plant_with_slug(self, db):
        """Test slug generation handles duplicates."""
        user = UserFactory()
        
        # Create first plant
        plant1 = Plant.create_user_plant(
            user=user,
            common_name="Duplicate Plant",
            water_interval=5
        )
        
        # Base slug should be used for first plant
        assert plant1.slug == "user-plant-duplicate-plant"
        
        # Create second plant with same name
        plant2 = Plant.create_user_plant(
            user=user,
            common_name="Duplicate Plant",
            water_interval=5
        )
        
        # Second plant should have different slug
        assert plant2.slug != plant1.slug
        assert plant2.slug.startswith("user-plant-duplicate-plant")


@pytest.mark.unit
class TestPlantSaveBehavior:
    """Test the custom save behavior of the Plant model."""
    
    def test_save_api_plant_by_admin(self, db):
        """Test admin can directly save changes to API plants."""
        admin = AdminFactory()
        plant = APIPlantFactory()
        
        # Change a field
        plant.common_name = "Updated Name"
        
        # Save with admin user
        plant.save(user=admin)
        
        # Changes should be applied
        updated_plant = Plant.objects.get(id=plant.id)
        assert updated_plant.common_name == "Updated Name"
    
    def test_save_api_plant_by_user_creates_change_request(self, db):
        """Test regular user changes to API plants create change requests."""
        user = UserFactory()
        plant = APIPlantFactory(water_interval=7)
        
        # Original state
        original_water_interval = plant.water_interval
        
        # Change a user-editable field
        plant.water_interval = 10
        
        # Save with regular user - this should create a change request
        plant.save(user=user)
        
        # Original plant should be unchanged
        refreshed_plant = Plant.objects.get(id=plant.id)
        assert refreshed_plant.water_interval == original_water_interval
        
        # A change request should exist
        change_request = PlantChangeRequest.objects.filter(
            plant=plant,
            user=user,
            field_name='water_interval'
        ).first()
        
        assert change_request is not None
        assert change_request.old_value == str(original_water_interval)
        assert change_request.new_value == '10'
        assert change_request.status == 'PENDING'
    
    def test_user_can_edit_own_plant(self, db):
        """Test user can edit plants they created."""
        user = UserFactory()
        plant = UserCreatedPlantFactory(created_by=user)
        
        # Change a field
        plant.common_name = "My Updated Plant"
        
        # Save with owner user
        plant.save(user=user)
        
        # Changes should be applied
        updated_plant = Plant.objects.get(id=plant.id)
        assert updated_plant.common_name == "My Updated Plant"
    
    def test_user_cannot_edit_others_plant(self, db):
        """Test user cannot edit plants created by others."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        plant = UserCreatedPlantFactory(created_by=user1)
        
        # Change a field
        plant.common_name = "Unauthorized Change"
        
        # Try to save with non-owner user
        with pytest.raises(PermissionDenied):
            plant.save(user=user2)
    
    def test_direct_save_skips_permissions(self, db):
        """Test direct_save parameter bypasses permission checks."""
        plant = APIPlantFactory(common_name="Original Name")
        
        # Change value
        plant.common_name = "Direct Changed Name"
        
        # Save with direct_save flag
        plant.save(direct_save=True)
        
        # Changes should be applied
        updated_plant = Plant.objects.get(id=plant.id)
        assert updated_plant.common_name == "Direct Changed Name"


@pytest.mark.unit
class TestPlantChangeRequestModel:
    """Test the PlantChangeRequest model."""
    
    def test_create_change_request(self, db):
        """Test creating a change request."""
        plant = APIPlantFactory()
        user = UserFactory()
        
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name='water_interval',
            old_value='7',
            new_value='5'
        )
        
        assert change_request.id is not None
        assert change_request.status == 'PENDING'
        assert change_request.created_at is not None
    
    def test_approve_change_request(self, db):
        """Test approving a change request applies the change to the plant."""
        plant = APIPlantFactory(water_interval=7)
        user = UserFactory()
        admin = AdminFactory()
        
        # Create change request
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name='water_interval',
            old_value='7',
            new_value='5'
        )
        
        # Approve the change
        change_request.approve(reviewer=admin)
        
        # Check request was updated
        assert change_request.status == 'APPROVED'
        assert change_request.reviewer == admin
        
        # Check plant was updated
        updated_plant = Plant.objects.get(id=plant.id)
        assert updated_plant.water_interval == 5
    
    def test_reject_change_request(self, db):
        """Test rejecting a change request."""
        plant = APIPlantFactory(water_interval=7)
        user = UserFactory()
        admin = AdminFactory()
        
        # Original state
        original_water_interval = plant.water_interval
        
        # Create change request
        change_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name='water_interval',
            old_value='7',
            new_value='5'
        )
        
        # Reject the change
        change_request.reject(
            reviewer=admin,
            notes="Plant doesn't need this change."
        )
        
        # Check request was updated
        assert change_request.status == 'REJECTED'
        assert change_request.reviewer == admin
        assert change_request.review_notes == "Plant doesn't need this change."
        
        # Check plant was not updated
        updated_plant = Plant.objects.get(id=plant.id)
        assert updated_plant.water_interval == original_water_interval
    
    def test_post_generation_hooks(self, db):
        """Test factory post-generation hooks for change requests."""
        plant = APIPlantFactory()
        user = UserFactory()
        
        # Create approved change request
        approved_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name='water_interval',
            old_value='7',
            new_value='5',
            approved=True  # Trigger post-generation hook
        )
        
        assert approved_request.status == 'APPROVED'
        assert approved_request.reviewer is not None
        
        # Create rejected change request
        rejected_request = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name='water_interval',
            old_value='7',
            new_value='3',
            rejected=True  # Trigger post-generation hook
        )
        
        assert rejected_request.status == 'REJECTED'
        assert rejected_request.reviewer is not None
        assert rejected_request.review_notes is not None