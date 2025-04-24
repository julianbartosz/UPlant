# backend/root/plants/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.db import models
from plants.models import Plant, PlantChangeRequest
from django import forms

class PlantChangeRequestInline(admin.TabularInline):
    """Inline view of change requests for a plant"""
    model = PlantChangeRequest
    extra = 0
    fields = ['field_name', 'old_value', 'new_value', 'user', 'status', 'created_at']
    readonly_fields = ['field_name', 'old_value', 'new_value', 'user', 'created_at']
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False
        
    def has_change_permission(self, request, obj=None):
        # Allow viewing but not editing directly from here
        return True

class PlantAdminForm(forms.ModelForm):
    class Meta:
        model = Plant
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Convert empty strings to None for nullable boolean fields
        boolean_fields = ['flower_conspicuous', 'foliage_retention', 
                          'fruit_or_seed_conspicuous', 'fruit_or_seed_persistence']
        
        for field in boolean_fields:
            if field in cleaned_data and cleaned_data[field] == '':
                cleaned_data[field] = None
                
        return cleaned_data

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """Admin interface for Plant model"""
    form = PlantAdminForm  # Use custom form
    
    def save_model(self, request, obj, form, change):
        """Override save_model to handle boolean fields before validation"""
        # Convert empty strings to None for these boolean fields
        boolean_fields = ['flower_conspicuous', 'foliage_retention', 
                          'fruit_or_seed_conspicuous', 'fruit_or_seed_persistence']
        
        for field in boolean_fields:
            if hasattr(obj, field) and getattr(obj, field) == '':
                setattr(obj, field, None)
        
        # Pass direct_save=True to bypass full_clean in the model's save method
        obj.save(direct_save=True)
    
    list_display = [
        'id', 'common_name', 'scientific_name', 'is_user_created', 
        'is_verified', 'created_by', 'pending_changes', 'created_at'
    ]
    list_filter = [
        'is_user_created', 'is_verified', 'vegetable', 'edible',
        'status', 'rank', 'family', 'created_at'
    ]
    search_fields = [
        'common_name', 'scientific_name', 'slug', 'family',
        'family_common_name', 'genus'
    ]
    readonly_fields = ['created_at', 'updated_at', 'api_id']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['verify_plants', 'unverify_plants']
    inlines = [PlantChangeRequestInline]
    
    # Custom admin forms for different scenarios
    fieldsets = [
        ('Basic Information', {
            'fields': ['common_name', 'scientific_name', 'slug', 'image_url']
        }),
        ('Taxonomy', {
            'fields': ['family', 'family_common_name', 'genus', 'genus_id', 'rank', 'status', 'api_id'],
            'classes': ['collapse']
        }),
        ('Plant Characteristics', {
            'fields': ['vegetable', 'duration', 'edible', 'edible_part', 'flower_color', 
                      'flower_conspicuous', 'foliage_texture', 'foliage_color', 
                      'foliage_retention', 'toxicity'],
            'classes': ['collapse']
        }),
        ('Growing Information', {
            'fields': ['water_interval', 'sunlight_requirements', 'soil_type', 
                     'days_to_harvest', 'min_temperature', 'max_temperature',
                     'ph_minimum', 'ph_maximum', 'light', 'atmospheric_humidity'],
            'classes': ['collapse']
        }),
        ('Additional Growing Details', {
            'fields': [
                'row_spacing_cm', 'spread_cm', 'minimum_precipitation', 
                'maximum_precipitation', 'minimum_root_depth', 'growth_rate',
                'average_height', 'maximum_height'
            ],
            'classes': ['collapse']
        }),
        ('Seasonal Information', {
            'fields': ['growth_months', 'bloom_months', 'fruit_months'],
            'classes': ['collapse']
        }),
        ('Care Instructions', {
            'fields': ['detailed_description', 'care_instructions', 'nutrient_requirements',
                     'maintenance_notes', 'sowing'],
        }),
        ('Metadata', {
            'fields': ['is_user_created', 'created_by', 'is_verified', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def pending_changes(self, obj):
        """Display the number of pending change requests with a link"""
        count = obj.change_requests.filter(status='PENDING').count()
        if count > 0:
            url = reverse('admin:plants_plantchangerequest_changelist') + f'?plant__id__exact={obj.id}&status__exact=PENDING'
            return format_html('<a href="{}">{} pending</a>', url, count)
        return '0'
    pending_changes.short_description = 'Change Requests'

    def verify_plants(self, request, queryset):
        """Mark selected plants as verified"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} plants marked as verified.")
    verify_plants.short_description = "Mark selected plants as verified"

    def unverify_plants(self, request, queryset):
        """Mark selected plants as unverified"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} plants marked as unverified.")
    unverify_plants.short_description = "Mark selected plants as unverified"
    
    def get_queryset(self, request):
        """Add annotation for number of pending change requests"""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _pending_changes=Count('change_requests', filter=models.Q(change_requests__status='PENDING'))
        )

@admin.register(PlantChangeRequest)
class PlantChangeRequestAdmin(admin.ModelAdmin):
    """Admin interface for PlantChangeRequest model"""
    list_display = [
        'id', 'plant_link', 'field_name', 'truncated_old_value', 'truncated_new_value', 
        'user', 'status', 'created_at'
    ]
    list_filter = ['status', 'field_name', 'created_at']
    search_fields = ['plant__common_name', 'plant__scientific_name', 'user__username', 'field_name']
    readonly_fields = ['field_name', 'old_value', 'new_value', 'plant', 'user', 'created_at', 'updated_at']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['approve_changes', 'reject_changes']
    
    fieldsets = [
        ('Change Information', {
            'fields': ['plant', 'field_name', 'old_value', 'new_value', 'reason']
        }),
        ('Review Status', {
            'fields': ['status', 'reviewer', 'review_notes']
        }),
        ('Metadata', {
            'fields': ['user', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def plant_link(self, obj):
        """Display a link to the plant"""
        url = reverse('admin:plants_plant_change', args=[obj.plant.id])
        return format_html('<a href="{}">{}</a>', url, obj.plant)
    plant_link.short_description = 'Plant'
    
    def truncated_old_value(self, obj):
        """Display truncated old value"""
        if obj.old_value and len(obj.old_value) > 50:
            return f"{obj.old_value[:47]}..."
        return obj.old_value
    truncated_old_value.short_description = 'Old Value'
    
    def truncated_new_value(self, obj):
        """Display truncated new value"""
        if obj.new_value and len(obj.new_value) > 50:
            return f"{obj.new_value[:47]}..."
        return obj.new_value
    truncated_new_value.short_description = 'New Value'
    
    def approve_changes(self, request, queryset):
        """Approve selected change requests"""
        for change_request in queryset.filter(status='PENDING'):
            change_request.approve(reviewer=request.user)
        self.message_user(request, f"{queryset.count()} change requests approved and applied.")
    approve_changes.short_description = "Approve selected change requests"
    
    def reject_changes(self, request, queryset):
        """Reject selected change requests"""
        for change_request in queryset.filter(status='PENDING'):
            change_request.reject(reviewer=request.user)
        self.message_user(request, f"{queryset.count()} change requests rejected.")
    reject_changes.short_description = "Reject selected change requests"