# backend/root/gardens/api/serializers.py

from rest_framework import serializers
from gardens.models import Garden, GardenLog
from plants.api.serializers import PlantBaseSerializer

class GardenLogSerializer(serializers.ModelSerializer):
    plant_details = PlantBaseSerializer(source='plant', read_only=True)
    
    class Meta:
        model = GardenLog
        fields = ['id', 'garden', 'plant', 'plant_details', 'x_coordinate', 'y_coordinate', 
                 'planted_date', 'notes', 'health_status', 'last_watered', 
                 'last_fertilized', 'last_pruned', 'growth_stage']
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate garden log data."""
        # Check if garden was provided
        if 'garden' not in data:
            raise serializers.ValidationError({"garden": "Garden is required"})
            
        # Check if plant was provided
        if 'plant' not in data:
            raise serializers.ValidationError({"plant": "Plant is required"})
            
        # Check coordinates
        if 'x_coordinate' not in data:
            raise serializers.ValidationError({"x_coordinate": "X coordinate is required"})
            
        if 'y_coordinate' not in data:
            raise serializers.ValidationError({"y_coordinate": "Y coordinate is required"})
        
        # Validate coordinates are within garden boundaries
        garden = data['garden']
        x = data['x_coordinate']
        y = data['y_coordinate']
        
        if x < 0 or x >= garden.size_x:
            raise serializers.ValidationError(
                {"x_coordinate": f"X coordinate must be between 0 and {garden.size_x - 1}"}
            )
            
        if y < 0 or y >= garden.size_y:
            raise serializers.ValidationError(
                {"y_coordinate": f"Y coordinate must be between 0 and {garden.size_y - 1}"}
            )
            
        # Check for existing plant at same position (excluding soft-deleted ones)
        existing = GardenLog.objects.filter(
            garden=garden,
            x_coordinate=x,
            y_coordinate=y,
            is_deleted=False
        )
        
        # If we're updating an existing log, exclude it from the check
        instance = getattr(self, 'instance', None)
        if instance:
            existing = existing.exclude(id=instance.id)
            
        if existing.exists():
            raise serializers.ValidationError(
                {"position": f"A plant already exists at position ({x}, {y})"}
            )
        
        return data
    
    
class GardenSerializer(serializers.ModelSerializer):
    garden_logs = GardenLogSerializer(many=True, read_only=True, source='logs')
    total_plants = serializers.SerializerMethodField()
    
    class Meta:
        model = Garden
        fields = ['id', 'name', 'size_x', 'size_y', 'created_at', 
                 'garden_logs', 'total_plants', 'user']
        read_only_fields = ['user']
    
    def get_total_plants(self, obj):
        return obj.logs.count()
    
    def create(self, validated_data):
        # Assign the current user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GardenGridSerializer(serializers.ModelSerializer):
    """Serializer for the garden grid layout needed by the frontend"""
    cells = serializers.SerializerMethodField()
    x = serializers.IntegerField(source='size_x')
    y = serializers.IntegerField(source='size_y')
    
    class Meta:
        model = Garden
        fields = ['id', 'name', 'x', 'y', 'cells']
    
    def get_cells(self, obj):
        # Initialize empty grid based on garden dimensions
        grid = [[None for _ in range(obj.size_x)] for _ in range(obj.size_y)]
        
        # Fill in plants where they exist in the garden logs
        garden_logs = obj.logs.select_related('plant').all()
        
        for log in garden_logs:
            if 0 <= log.y_coordinate < obj.size_y and 0 <= log.x_coordinate < obj.size_x:
                # Create a simplified plant object for the frontend
                plant_data = {
                    'id': log.plant.id,
                    'common_name': log.plant.common_name,
                    'scientific_name': log.plant.scientific_name,
                    'family': log.plant.family or 'default',
                    'health_status': log.health_status,
                    'log_id': log.id
                }
                grid[log.y_coordinate][log.x_coordinate] = plant_data
                
        return grid