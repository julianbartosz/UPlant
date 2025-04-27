import pytest
from unittest.mock import patch, Mock
from django import forms
from django.core.exceptions import ValidationError

from plants.forms import (
    PlantForm, 
    UserPlantCreateForm, 
    UserPlantEditForm,
    PlantChangeRequestForm,
    AdminPlantForm
)
from plants.models import Plant, PlantChangeRequest
from plants.tests.factories import (
    APIPlantFactory,
    UserCreatedPlantFactory,
    PlantWithFullDetailsFactory
)
from user_management.tests.factories import UserFactory, AdminFactory


@pytest.mark.unit
class TestPlantFormBase:
    """Test the base PlantForm functionality shared by all plant forms."""
    
    def test_init_with_user(self, db):
        """Test form initialization with user parameter."""
        user = UserFactory()
        form = PlantForm(user=user)
        
        # User should be stored on the form
        assert form.user == user
    
    def test_help_text_added_from_model(self, db):
        """Test that help text is added from model to form fields."""
        # Create a test plant model instance with a field that has help text
        plant = APIPlantFactory()
        
        # Get the water_interval field which has help text in the model
        field = Plant._meta.get_field('water_interval')
        original_help_text = field.help_text
        assert original_help_text, "Test requires a field with help text"
        
        # Initialize form for this instance
        form = PlantForm(instance=plant)
        
        # Form field should have the same help text as model field
        assert form.fields['water_interval'].help_text == original_help_text
    
    def test_bootstrap_classes_added(self, db):
        """Test that Bootstrap classes are added to all fields."""
        form = PlantForm()
        
        # All fields should have the form-control class
        for field in form.fields.values():
            assert 'form-control' in field.widget.attrs.get('class', '')
    
    def test_bootstrap_classes_preserved(self, db):
        """Test that existing Bootstrap classes are preserved."""
        # Create a subclass with a field that has existing classes
        class TestForm(PlantForm):
            test_field = forms.CharField(widget=forms.TextInput(attrs={'class': 'existing-class'}))
            
        form = TestForm()
        
        # Field should have both existing class and form-control
        assert form.fields['test_field'].widget.attrs['class'] == 'existing-class'


@pytest.mark.unit
class TestUserPlantCreateForm:
    """Test the UserPlantCreateForm for creating user plants."""
    
    def test_form_fields(self, db):
        """Test form has correct fields."""
        form = UserPlantCreateForm()
        
        expected_fields = [
            'common_name', 'scientific_name', 'image_url', 'water_interval',
            'sunlight_requirements', 'soil_type', 'min_temperature',
            'max_temperature', 'detailed_description', 'care_instructions'
        ]
        
        for field in expected_fields:
            assert field in form.fields
    
    def test_required_fields_marked(self, db):
        """Test that required fields are marked as required."""
        form = UserPlantCreateForm()
        
        # Check each user required field is marked required in the form
        for field_name in Plant.USER_REQUIRED_FIELDS:
            if field_name in form.fields:
                assert form.fields[field_name].required is True
                assert form.fields[field_name].widget.attrs.get('required') is True
                assert '*' in form.fields[field_name].label
    
    def test_scientific_name_optional(self, db):
        """Test that scientific_name is optional."""
        form = UserPlantCreateForm()
        assert form.fields['scientific_name'].required is False
    
    def test_custom_widgets(self, db):
        """Test that custom widgets are properly configured."""
        form = UserPlantCreateForm()
        
        # Check textarea fields have correct row settings
        assert form.fields['detailed_description'].widget.attrs['rows'] == 4
        assert form.fields['care_instructions'].widget.attrs['rows'] == 4
        
        # Check placeholders
        assert 'placeholder' in form.fields['common_name'].widget.attrs
        assert 'placeholder' in form.fields['scientific_name'].widget.attrs
        assert 'placeholder' in form.fields['image_url'].widget.attrs
    
    def test_valid_form_submission(self, db):
        """Test that a valid form submission passes validation."""
        user = UserFactory()
        
        form_data = {
            'common_name': 'Test Plant',
            'water_interval': 5,
            'sunlight_requirements': 'Full Sun',
            'soil_type': 'Loamy'
        }
        
        form = UserPlantCreateForm(data=form_data, user=user)
        
        assert form.is_valid(), f"Form validation failed with errors: {form.errors}"
    
    def test_temperature_range_validation(self, db):
        """Test validation of temperature range."""
        user = UserFactory()
        
        # Invalid form with min > max temperature
        form_data = {
            'common_name': 'Test Plant',
            'water_interval': 5,
            'min_temperature': 30,
            'max_temperature': 20
        }
        
        form = UserPlantCreateForm(data=form_data, user=user)
        assert not form.is_valid()
        assert 'min_temperature' in form.errors
        assert 'max_temperature' in form.errors
        
        # Valid form with min < max temperature
        form_data = {
            'common_name': 'Test Plant',
            'water_interval': 5,
            'min_temperature': 10,
            'max_temperature': 30
        }
        
        form = UserPlantCreateForm(data=form_data, user=user)
        assert form.is_valid(), f"Form validation failed with errors: {form.errors}"
    
    def test_form_save_creates_user_plant(self, db):
        """Test that saving the form creates a user plant."""
        user = UserFactory()
        
        form_data = {
            'common_name': 'My Created Plant',
            'water_interval': 7,
            'sunlight_requirements': 'Partial Shade',
            'soil_type': 'Well-draining'
        }
        
        form = UserPlantCreateForm(data=form_data, user=user)
        
        with patch('plants.models.Plant.create_user_plant') as mock_create:
            mock_create.return_value = Plant(id=999)
            form.is_valid()
            form.save()
            
            # Check that create_user_plant was called with correct args
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs['common_name'] == 'My Created Plant'
            assert call_kwargs['water_interval'] == 7
    
    def test_form_save_without_user(self, db):
        """Test that save fails without a user."""
        form_data = {
            'common_name': 'My Created Plant',
            'water_interval': 7
        }
        
        form = UserPlantCreateForm(data=form_data)
        form.is_valid()
        
        with pytest.raises(ValueError, match="User must be provided"):
            form.save()
    
    def test_form_save_without_commit(self, db):
        """Test save with commit=False."""
        user = UserFactory()
        
        form_data = {
            'common_name': 'My Created Plant',
            'water_interval': 7,
            'sunlight_requirements': 'Partial Shade',
            'soil_type': 'Well-draining'
        }
        
        form = UserPlantCreateForm(data=form_data, user=user)
        
        with patch('plants.models.Plant.create_user_plant') as mock_create:
            # Create_user_plant shouldn't be called with commit=False
            form.is_valid()
            instance = form.save(commit=False)
            
            mock_create.assert_not_called()
            assert isinstance(instance, Plant)


@pytest.mark.unit
class TestUserPlantEditForm:
    """Test the UserPlantEditForm for editing user plants."""
    
    def test_form_fields(self, db):
        """Test that form has user-editable fields."""
        form = UserPlantEditForm()
        
        # All user editable fields should be in the form
        for field in Plant.USER_EDITABLE_FIELDS:
            assert field in form.fields
    
    def test_fieldsets(self, db):
        """Test that form has fieldsets defined."""
        form = UserPlantEditForm()
        
        assert hasattr(form, 'fieldsets')
        assert len(form.fieldsets) == 3
        
        # Check fieldset structure
        assert form.fieldsets[0][0] == 'Basic Information'
        assert 'common_name' in form.fieldsets[0][1]
        
        assert form.fieldsets[1][0] == 'Care Requirements'
        assert 'water_interval' in form.fieldsets[1][1]
        
        assert form.fieldsets[2][0] == 'Detailed Information'
        assert 'detailed_description' in form.fieldsets[2][1]
    
    def test_required_fields(self, db):
        """Test that required fields are marked as required."""
        form = UserPlantEditForm()
        
        for field_name in Plant.USER_REQUIRED_FIELDS:
            if field_name in form.fields:
                assert form.fields[field_name].required is True
    
    def test_temperature_validation(self, db):
        """Test temperature range validation."""
        user = UserFactory()
        plant = UserCreatedPlantFactory(created_by=user)
        
        # Invalid form with min > max temperature
        form_data = {
            'common_name': plant.common_name,
            'water_interval': plant.water_interval,
            'min_temperature': 30,
            'max_temperature': 20
        }
        
        form = UserPlantEditForm(data=form_data, instance=plant, user=user)
        assert not form.is_valid()
        assert 'min_temperature' in form.errors
        assert 'max_temperature' in form.errors
    
    def test_form_save_calls_save_with_user(self, db):
        """Test that save passes the user to model save method."""
        user = UserFactory()
        plant = UserCreatedPlantFactory(created_by=user)
        
        form_data = {
            'common_name': 'Updated Plant Name',
            'water_interval': plant.water_interval,
            'sunlight_requirements': plant.sunlight_requirements,
            'soil_type': plant.soil_type
        }
        
        form = UserPlantEditForm(data=form_data, instance=plant, user=user)
        
        with patch.object(Plant, 'save') as mock_save:
            form.is_valid()
            form.save()
            
            # Check that save was called with user
            mock_save.assert_called_once()
            assert mock_save.call_args[1].get('user') == user
    
    def test_form_save_without_user(self, db):
        """Test that save fails without a user."""
        plant = UserCreatedPlantFactory()
        
        form_data = {
            'common_name': 'Updated Plant Name',
            'water_interval': plant.water_interval
        }
        
        form = UserPlantEditForm(data=form_data, instance=plant)
        form.is_valid()
        
        with pytest.raises(ValueError, match="User must be provided"):
            form.save()


@pytest.mark.unit
class TestPlantChangeRequestForm:
    """Test the PlantChangeRequestForm for suggesting changes."""
    
    def test_form_fields(self, db):
        """Test form has correct fields."""
        form = PlantChangeRequestForm()
        
        expected_fields = ['field_name', 'new_value', 'reason']
        for field in expected_fields:
            assert field in form.fields
    
    def test_init_with_field_name(self, db):
        """Test initialization with a specific field name."""
        plant = APIPlantFactory(water_interval=7)
        form = PlantChangeRequestForm(plant=plant, field_name='water_interval')
        
        # Field name should be hidden and preset
        assert isinstance(form.fields['field_name'].widget, forms.HiddenInput)
        assert form.fields['field_name'].initial == 'water_interval'
        
        # New value should have custom label and help text
        assert 'Water Interval' in form.fields['new_value'].label
        assert 'Current value: 7' in form.fields['new_value'].help_text
    
    def test_init_without_field_name(self, db):
        """Test initialization without a specific field name."""
        form = PlantChangeRequestForm()
        
        # Field name should be a choice field with user editable fields
        assert isinstance(form.fields['field_name'], forms.ChoiceField)
        
        # Choices should be all user-editable fields
        choices = dict(form.fields['field_name'].choices)
        for field in Plant.USER_EDITABLE_FIELDS:
            field_label = field.replace('_', ' ').title()
            assert field_label in choices.values()
    
    def test_clean_validates_plant_and_user(self, db):
        """Test clean validates that plant and user are set."""
        form = PlantChangeRequestForm(data={
            'field_name': 'water_interval',
            'new_value': '5',
            'reason': 'Testing'
        })
        
        # Form should not be valid without plant and user
        assert not form.is_valid()
        assert "Plant must be provided" in str(form.errors)
    
    def test_clean_validates_editable_fields(self, db):
        """Test that only user editable fields are allowed."""
        plant = APIPlantFactory()
        user = UserFactory()
        
        # Try to edit non-editable field
        form = PlantChangeRequestForm(
            data={
                'field_name': 'api_id',  # Non-editable field
                'new_value': '12345',
                'reason': 'Testing'
            },
            plant=plant,
            user=user
        )
        
        assert not form.is_valid()
        assert "cannot be edited by users" in str(form.errors['field_name'])
        
        # Try to edit editable field
        form = PlantChangeRequestForm(
            data={
                'field_name': 'water_interval',  # Editable field
                'new_value': '5',
                'reason': 'Testing'
            },
            plant=plant,
            user=user
        )
        
        assert form.is_valid()
    
    def test_save_sets_plant_user_and_old_value(self, db):
        """Test save sets plant, user, and old value."""
        plant = APIPlantFactory(water_interval=7)
        user = UserFactory()
        
        form = PlantChangeRequestForm(
            data={
                'field_name': 'water_interval',
                'new_value': '5',
                'reason': 'Testing'
            },
            plant=plant,
            user=user
        )
        
        assert form.is_valid()
        change_request = form.save()
        
        assert change_request.plant == plant
        assert change_request.user == user
        assert change_request.old_value == '7'
        assert change_request.new_value == '5'
    
    def test_save_without_commit(self, db):
        """Test save with commit=False."""
        plant = APIPlantFactory(water_interval=7)
        user = UserFactory()
        
        form = PlantChangeRequestForm(
            data={
                'field_name': 'water_interval',
                'new_value': '5',
                'reason': 'Testing'
            },
            plant=plant,
            user=user
        )
        
        assert form.is_valid()
        change_request = form.save(commit=False)
        
        # Object should be configured but not saved to database
        assert change_request.plant == plant
        assert change_request.user == user
        assert change_request.old_value == '7'
        assert change_request.id is None  # Not saved to DB yet


@pytest.mark.unit
class TestAdminPlantForm:
    """Test the AdminPlantForm for admin editing."""
    
    def test_form_has_all_fields(self, db):
        """Test form includes all model fields."""
        form = AdminPlantForm()
        model_fields = [f.name for f in Plant._meta.fields]
        
        # All model fields should be in the form
        for field in model_fields:
            assert field in form.fields
    
    def test_widget_customization(self, db):
        """Test that widgets are customized as expected."""
        form = AdminPlantForm()
        
        # Check textarea fields have correct row settings
        textarea_fields = [
            'synonyms', 'edible_part', 'flower_color', 'foliage_color',
            'fruit_or_seed_color', 'detailed_description', 'care_instructions',
            'growth_months', 'bloom_months', 'fruit_months'
        ]
        
        for field_name in textarea_fields:
            assert isinstance(form.fields[field_name].widget, forms.Textarea)
            assert 'rows' in form.fields[field_name].widget.attrs


@pytest.mark.integration
class TestFormIntegration:
    """Test forms working together in real scenarios."""
    
    def test_create_then_edit_plant(self, db):
        """Test creating a plant and then editing it."""
        user = UserFactory()
        
        # Create a plant
        create_data = {
            'common_name': 'Integration Test Plant',
            'water_interval': 5,
            'sunlight_requirements': 'Full Sun',
            'soil_type': 'Rich'
        }
        
        create_form = UserPlantCreateForm(data=create_data, user=user)
        assert create_form.is_valid()
        plant = create_form.save()
        
        # Now edit the plant
        edit_data = {
            'common_name': 'Updated Test Plant',
            'water_interval': 7,
            'sunlight_requirements': 'Partial Shade',
            'soil_type': 'Rich',
            'detailed_description': 'New plant description'
        }
        
        edit_form = UserPlantEditForm(data=edit_data, instance=plant, user=user)
        assert edit_form.is_valid()
        updated_plant = edit_form.save()
        
        # Check that plant was updated
        assert updated_plant.common_name == 'Updated Test Plant'
        assert updated_plant.water_interval == 7
        assert updated_plant.sunlight_requirements == 'Partial Shade'
        assert updated_plant.detailed_description == 'New plant description'
    
    def test_submit_change_request(self, db):
        """Test submitting a change request for a plant."""
        user = UserFactory()
        plant = APIPlantFactory(water_interval=10)
        
        # Create a change request
        request_data = {
            'field_name': 'water_interval',
            'new_value': '7',
            'reason': 'This plant needs less water'
        }
        
        form = PlantChangeRequestForm(data=request_data, plant=plant, user=user)
        assert form.is_valid()
        change_request = form.save()
        
        # Check that change request was created
        assert change_request.id is not None
        assert change_request.plant == plant
        assert change_request.user == user
        assert change_request.field_name == 'water_interval'
        assert change_request.old_value == '10'
        assert change_request.new_value == '7'
        assert change_request.reason == 'This plant needs less water'
        assert change_request.status == 'PENDING'