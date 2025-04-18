# backend/root/gardens/api/serializers.py

from rest_framework import serializers
from gardens.models import Garden, GardenLog
from plants.api.serializers import PlantBaseSerializer

class GardenLogSerializer(serializers.ModelSerializer):
    # Update this to use PlantBaseSerializer instead
    plant_details = PlantBaseSerializer(source='plant', read_only=True)
    
    class Meta:
        model = GardenLog
        fields = ['id', 'plant', 'plant_details', 'x_position', 'y_position', 
                 'planted_date', 'notes', 'health_status', 'last_watered']

class GardenSerializer(serializers.ModelSerializer):
    garden_logs = GardenLogSerializer(many=True, read_only=True, source='gardenlog_set')
    total_plants = serializers.SerializerMethodField()
    
    class Meta:
        model = Garden
        fields = ['id', 'name', 'size_x', 'size_y', 'created_at', 
                 'garden_logs', 'total_plants', 'user']
        read_only_fields = ['user']
    
    def get_total_plants(self, obj):
        return obj.gardenlog_set.count()
    
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
        garden_logs = obj.gardenlog_set.select_related('plant').all()
        
        for log in garden_logs:
            if 0 <= log.y_position < obj.size_y and 0 <= log.x_position < obj.size_x:
                # Create a simplified plant object for the frontend
                plant_data = {
                    'id': log.plant.id,
                    'common_name': log.plant.common_name,
                    'scientific_name': log.plant.scientific_name,
                    'family': log.plant.family or 'default',
                    'health_status': log.health_status,
                    'log_id': log.id
                }
                grid[log.y_position][log.x_position] = plant_data
                
        return grid