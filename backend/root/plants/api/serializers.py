# backend/root/plants/api/serializers.py

from rest_framework import serializers
from django.utils.text import slugify
from plants.models import Plant, PlantChangeRequest
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user representation for related fields"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class PlantBaseSerializer(serializers.ModelSerializer):
    """Base serializer with common plant fields"""
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Plant
        fields = [
            'id', 'common_name', 'scientific_name', 'slug', 
            'image_url', 'is_user_created', 'is_verified',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None

class PlantDetailSerializer(PlantBaseSerializer):
    """Full read-only serializer for plant details"""
    pending_changes = serializers.SerializerMethodField()
    
    class Meta(PlantBaseSerializer.Meta):
        fields = PlantBaseSerializer.Meta.fields + [
            'api_id', 'status', 'rank', 'family_common_name', 'family', 
            'genus_id', 'genus', 'synonyms', 'vegetable', 'duration', 
            'edible', 'edible_part', 'flower_color', 'flower_conspicuous', 
            'foliage_texture', 'foliage_color', 'foliage_retention', 
            'fruit_or_seed_conspicuous', 'fruit_or_seed_color', 
            'fruit_or_seed_shape', 'fruit_or_seed_persistence',
            'row_spacing_cm', 'spread_cm', 'days_to_harvest', 
            'sowing', 'ph_minimum', 'ph_maximum', 'light', 
            'atmospheric_humidity', 'minimum_precipitation', 'maximum_precipitation',
            'minimum_root_depth', 'growth_months', 'bloom_months', 
            'fruit_months', 'growth_rate', 'average_height', 'maximum_height',
            'toxicity', 'water_interval', 'sunlight_requirements', 'soil_type',
            'min_temperature', 'max_temperature', 'detailed_description',
            'care_instructions', 'nutrient_requirements', 'maintenance_notes',
            'pending_changes'
        ]
    
    def get_pending_changes(self, obj):
        """Return count of pending change requests"""
        # Only return this for staff/admin users
        request = self.context.get('request')
        if request and (request.user.is_staff or request.user.role in ('Admin', 'Moderator')):
            return obj.change_requests.filter(status='PENDING').count()
        return 0

class UserPlantCreateSerializer(serializers.ModelSerializer):
    """Serializer for users to create custom plants"""
    
    class Meta:
        model = Plant
        fields = [
            'common_name', 'scientific_name', 'image_url', 'water_interval',
            'sunlight_requirements', 'soil_type', 'min_temperature', 
            'max_temperature', 'detailed_description', 'care_instructions',
            'nutrient_requirements', 'maintenance_notes'
        ]
    
    def validate(self, data):
        """Validate required fields and constraints"""
        # Check required fields
        for field_name in Plant.USER_REQUIRED_FIELDS:
            if field_name not in data or data[field_name] in [None, '']:
                raise serializers.ValidationError({
                    field_name: f"{field_name} is required for user-created plants"
                })
                
        # Validate temperature range
        min_temp = data.get('min_temperature')
        max_temp = data.get('max_temperature')
        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise serializers.ValidationError({
                'min_temperature': 'Minimum temperature cannot be higher than maximum temperature',
                'max_temperature': 'Maximum temperature cannot be lower than minimum temperature'
            })
            
        return data
    
    def create(self, validated_data):
        """Create a new plant using the user plant factory method"""
        user = self.context['request'].user
        return Plant.create_user_plant(user, **validated_data)

class UserPlantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for users to update their own plants"""
    
    class Meta:
        model = Plant
        fields = Plant.USER_EDITABLE_FIELDS
        
    def validate(self, data):
        """Apply additional validation for user editable fields"""
        # Validate temperature range
        min_temp = data.get('min_temperature')
        max_temp = data.get('max_temperature')
        
        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise serializers.ValidationError({
                'min_temperature': 'Minimum temperature cannot be higher than maximum temperature',
                'max_temperature': 'Maximum temperature cannot be lower than minimum temperature'
            })
            
        # Get existing instance
        instance = getattr(self, 'instance', None)
        request = self.context.get('request')
        user = request.user if request else None
        
        # If this is an update, check if it's a Trefle plant
        # Users should use change requests for Trefle plants
        if instance and user and not (user.is_staff or user.role in ('Admin', 'Moderator')):
            is_trefle_plant = instance.api_id is not None and not instance.is_user_created
            if is_trefle_plant:
                raise serializers.ValidationError(
                    "You cannot directly edit a Trefle plant. Please submit a change request."
                )
                
        return data
    
    def update(self, instance, validated_data):
        """Update the plant with the validated data"""
        request = self.context.get('request')
        if request:
            # Pass user to save method for permission checking
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save(user=request.user)
            return instance
        return super().update(instance, validated_data)

class AdminPlantSerializer(serializers.ModelSerializer):
    """Full serializer for admin users to create/edit plants"""
    
    class Meta:
        model = Plant
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PlantChangeRequestSerializer(serializers.ModelSerializer):
    """Serializer for plant change requests"""
    user_details = UserMinimalSerializer(source='user', read_only=True)
    plant_details = PlantBaseSerializer(source='plant', read_only=True)
    reviewer_details = UserMinimalSerializer(source='reviewer', read_only=True)
    
    class Meta:
        model = PlantChangeRequest
        fields = [
            'id', 'plant', 'plant_details', 'user', 'user_details',
            'field_name', 'old_value', 'new_value', 'reason',
            'status', 'reviewer', 'reviewer_details', 'review_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'plant_details', 'user_details', 'reviewer_details',
            'old_value', 'status', 'reviewer', 'review_notes', 
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate the change request"""
        # Check if the field is editable by users
        field_name = data.get('field_name')
        if field_name not in Plant.USER_EDITABLE_FIELDS:
            raise serializers.ValidationError({
                'field_name': f"The field '{field_name}' cannot be edited by users"
            })
            
        return data
    
    def create(self, validated_data):
        """Create a change request with the current user"""
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Get the current value
        plant = validated_data.get('plant')
        field_name = validated_data.get('field_name')
        validated_data['old_value'] = getattr(plant, field_name, '')
        
        return super().create(validated_data)

class PlantChangeRequestCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating plant change requests"""
    
    class Meta:
        model = PlantChangeRequest
        fields = ['plant', 'field_name', 'new_value', 'reason']
        
    def validate(self, data):
        """Validate the change request"""
        plant = data.get('plant')
        field_name = data.get('field_name')
        
        # Check if the field is editable by users
        if field_name not in Plant.USER_EDITABLE_FIELDS:
            raise serializers.ValidationError({
                'field_name': f"The field '{field_name}' cannot be edited by users"
            })
            
        # Check if plant is not a user-created plant
        if plant.is_user_created:
            raise serializers.ValidationError(
                "Change requests are only for Trefle plants. User plants can be edited directly."
            )
            
        return data

class PlantListResponseSerializer(serializers.Serializer):
    """Wrapper serializer for API responses with pagination info"""
    data = serializers.ListField(child=PlantBaseSerializer())
    links = serializers.DictField(child=serializers.CharField())
    meta = serializers.DictField(child=serializers.IntegerField())

# External API serializers (for Trefle compatibility)
class TreflePlantSerializer(serializers.Serializer):
    """Serializer for external Trefle API plants"""
    id = serializers.IntegerField()
    common_name = serializers.CharField(allow_null=True, required=False)
    slug = serializers.CharField()
    scientific_name = serializers.CharField()
    status = serializers.CharField()
    rank = serializers.CharField()
    family_common_name = serializers.CharField(allow_null=True, required=False)
    family = serializers.CharField()
    genus_id = serializers.IntegerField()
    genus = serializers.CharField()
    image_url = serializers.URLField(allow_null=True, required=False)
    synonyms = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, required=False
    )
    # Expose a simplified links dictionary
    links = serializers.DictField(child=serializers.CharField(), required=False)

class TreflePlantListResponseSerializer(serializers.Serializer):
    """Wrapper serializer for Trefle API responses"""
    data = serializers.ListField(child=TreflePlantSerializer())
    links = serializers.DictField(child=serializers.CharField(), required=False)
    meta = serializers.DictField(child=serializers.IntegerField(), required=False)