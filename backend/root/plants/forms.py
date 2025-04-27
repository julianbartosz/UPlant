# backend/root/plants/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from plants.models import Plant, PlantChangeRequest

class PlantForm(forms.ModelForm):
    """Base form for plant models with common functionality."""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add help text from model to form fields
        for field_name, field in self.fields.items():
            model_field = self._meta.model._meta.get_field(field_name)
            if model_field.help_text and not field.help_text:
                field.help_text = model_field.help_text
                
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class UserPlantCreateForm(PlantForm):
    """Form for users to create custom plants with minimal information."""
    
    class Meta:
        model = Plant
        fields = ['common_name', 'scientific_name', 'image_url', 'water_interval',
                  'sunlight_requirements', 'soil_type', 'min_temperature', 
                  'max_temperature', 'detailed_description', 'care_instructions']
        widgets = {
            'common_name': forms.TextInput(attrs={'placeholder': 'E.g., Tomato, Basil, etc.'}),
            'scientific_name': forms.TextInput(attrs={'placeholder': 'Optional - will be auto-generated if left blank'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://example.com/plant-image.jpg'}),
            'detailed_description': forms.Textarea(attrs={'rows': 4}),
            'care_instructions': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'min_temperature': 'Minimum Temperature (°C)',
            'max_temperature': 'Maximum Temperature (°C)',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mark required fields
        for field_name in Plant.USER_REQUIRED_FIELDS:
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].widget.attrs['required'] = True
                # Add required star to label
                self.fields[field_name].label = f"{self.fields[field_name].label}*"
                
        # Make scientific name optional
        if 'scientific_name' in self.fields:
            self.fields['scientific_name'].required = False
    
    def clean(self):
        """Custom validation to check temperature range and other constraints."""
        cleaned_data = super().clean()
        
        min_temp = cleaned_data.get('min_temperature')
        max_temp = cleaned_data.get('max_temperature')
        
        if min_temp and max_temp and min_temp > max_temp:
            raise ValidationError({
                'min_temperature': 'Minimum temperature cannot be higher than maximum temperature',
                'max_temperature': 'Maximum temperature cannot be lower than minimum temperature'
            })
            
        return cleaned_data
    
    def save(self, commit=True):
        """Save the form and create a user plant."""
        if not self.user:
            raise ValueError("User must be provided to create a plant")
            
        if not commit:
            return super().save(commit=False)
            
        # Use the factory method to create user plant
        cleaned_data = {**self.cleaned_data}
        return Plant.create_user_plant(self.user, **cleaned_data)

class UserPlantEditForm(PlantForm):
    """Form for users to edit their own plants."""
    
    class Meta:
        model = Plant
        fields = Plant.USER_EDITABLE_FIELDS
        widgets = {
            'common_name': forms.TextInput(),
            'image_url': forms.URLInput(),
            'detailed_description': forms.Textarea(attrs={'rows': 4}),
            'care_instructions': forms.Textarea(attrs={'rows': 4}),
            'nutrient_requirements': forms.Textarea(attrs={'rows': 3}),
            'maintenance_notes': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Required fields
        for field_name in Plant.USER_REQUIRED_FIELDS:
            if field_name in self.fields:
                self.fields[field_name].required = True
                
        # Organize fields with fieldsets
        self.fieldsets = [
            ('Basic Information', ['common_name', 'image_url']),
            ('Care Requirements', [
                'water_interval', 'sunlight_requirements', 'soil_type', 
                'min_temperature', 'max_temperature'
            ]),
            ('Detailed Information', [
                'detailed_description', 'care_instructions', 
                'nutrient_requirements', 'maintenance_notes'
            ]),
        ]
    
    def clean(self):
        """Custom validation for plants."""
        cleaned_data = super().clean()
        
        # Temperature range validation
        min_temp = cleaned_data.get('min_temperature')
        max_temp = cleaned_data.get('max_temperature')
        
        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise ValidationError({
                'min_temperature': 'Minimum temperature cannot be higher than maximum temperature',
                'max_temperature': 'Maximum temperature cannot be lower than minimum temperature'
            })
            
        return cleaned_data
        
    def save(self, commit=True):
        """Save the form and verify user permissions."""
        if not self.user:
            raise ValueError("User must be provided to edit a plant")
            
        instance = super().save(commit=False)
        
        if commit:
            instance.save(user=self.user)
            
        return instance

class PlantChangeRequestForm(forms.ModelForm):
    """Form for users to suggest changes to Trefle plants."""
    
    class Meta:
        model = PlantChangeRequest
        fields = ['field_name', 'new_value', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Why are you suggesting this change?'}),
            'new_value': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Proposed new value'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.plant = kwargs.pop('plant', None)
        self.user = kwargs.pop('user', None)
        self.field_name = kwargs.pop('field_name', None)
        
        super().__init__(*args, **kwargs)
        
        # If field_name is provided, hide the field_name field
        if self.field_name:
            self.fields['field_name'].widget = forms.HiddenInput()
            self.fields['field_name'].initial = self.field_name
            
            # Set the label of new_value to the field name being edited
            field_label = self.field_name.replace('_', ' ').title()
            self.fields['new_value'].label = f"New {field_label}"
            
            # Get current value for context
            if self.plant:
                current_value = getattr(self.plant, self.field_name, '')
                self.fields['new_value'].help_text = f"Current value: {current_value}"
        else:
            # Only show editable fields in the dropdown
            editable_fields = []
            for field_name in Plant.USER_EDITABLE_FIELDS:
                field = Plant._meta.get_field(field_name)
                field_label = field_name.replace('_', ' ').title()
                editable_fields.append((field_name, field_label))
                
            self.fields['field_name'] = forms.ChoiceField(choices=editable_fields)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Make sure plant and user are provided
        if not self.plant:
            raise ValidationError("Plant must be provided to suggest changes")
            
        if not self.user:
            raise ValidationError("User must be provided to suggest changes")
            
        # Validate that the field is editable by users
        field_name = cleaned_data.get('field_name')
        if field_name not in Plant.USER_EDITABLE_FIELDS:
            raise ValidationError({
                'field_name': f"The field '{field_name}' cannot be edited by users"
            })
            
        return cleaned_data
    
    def save(self, commit=True):
        """Save the change request with the current plant and user."""
        instance = super().save(commit=False)
        
        # Set the plant and user
        instance.plant = self.plant
        instance.user = self.user
        
        # Get the current value of the field
        field_name = self.cleaned_data.get('field_name')
        instance.old_value = getattr(self.plant, field_name, '')
        
        if commit:
            instance.save()
            
        return instance

class AdminPlantForm(forms.ModelForm):
    """Full form for admins to edit all plant details."""
    
    class Meta:
        model = Plant
        fields = '__all__'
        widgets = {
            'synonyms': forms.Textarea(attrs={'rows': 2}),
            'edible_part': forms.Textarea(attrs={'rows': 2}),
            'flower_color': forms.Textarea(attrs={'rows': 2}),
            'foliage_color': forms.Textarea(attrs={'rows': 2}),
            'fruit_or_seed_color': forms.Textarea(attrs={'rows': 2}),
            'detailed_description': forms.Textarea(attrs={'rows': 5}),
            'care_instructions': forms.Textarea(attrs={'rows': 5}),
            'growth_months': forms.Textarea(attrs={'rows': 2}),
            'bloom_months': forms.Textarea(attrs={'rows': 2}),
            'fruit_months': forms.Textarea(attrs={'rows': 2}),
        }