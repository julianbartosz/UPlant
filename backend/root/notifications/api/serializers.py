# backend/root/notifications/api/serializers.py

from rest_framework import serializers
from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation
from plants.api.serializers import PlantDetailSerializer

class NotificationPlantAssociationSerializer(serializers.ModelSerializer):
    plant_details = PlantDetailSerializer(source='plant', read_only=True)
    
    class Meta:
        model = NotificationPlantAssociation
        fields = ['id', 'plant', 'plant_details', 'custom_interval']
        read_only_fields = ['id']


class NotificationInstanceSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = NotificationInstance
        fields = ['id', 'next_due', 'last_completed', 'status', 
                 'is_overdue', 'days_overdue', 'notification']
        read_only_fields = ['id', 'is_overdue', 'days_overdue']
    
    def get_days_overdue(self, obj):
        """Calculate days overdue for better frontend display"""
        if obj.is_overdue:
            from django.utils import timezone
            delta = timezone.now() - obj.next_due
            return delta.days
        return 0


class NotificationSerializer(serializers.ModelSerializer):
    plants = NotificationPlantAssociationSerializer(source='notificationplantassociation_set', 
                                                  many=True, read_only=True)
    garden_details = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    upcoming_instance = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'garden', 'garden_details', 'name', 'type', 'type_display',
                 'subtype', 'interval', 'plants', 'created_at', 'upcoming_instance']
        read_only_fields = ['id', 'created_at', 'type_display', 'garden_details', 'upcoming_instance']
    
    def get_garden_details(self, obj):
        """Return basic garden info"""
        return {
            'id': obj.garden.id,
            'name': obj.garden.name or f"Garden {obj.garden.id}"
        }
    
    def get_upcoming_instance(self, obj):
        """Return the next pending notification instance"""
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        if instance:
            return NotificationInstanceSerializer(instance).data
        return None
    
    def validate(self, data):
        """Validate notification data"""
        # Validate type and subtype consistency
        if data.get('type') != 'OT' and data.get('subtype'):
            raise serializers.ValidationError({
                'subtype': 'Subtype should only be used with "Other" notification types'
            })
        
        if data.get('type') == 'OT' and not data.get('subtype'):
            raise serializers.ValidationError({
                'subtype': 'Subtype is required for "Other" notification types'
            })
            
        # Ensure the garden belongs to the current user
        request = self.context.get('request')
        if request and request.user and data.get('garden'):
            if data['garden'].user != request.user:
                raise serializers.ValidationError({
                    'garden': 'You can only create notifications for your own gardens'
                })
        
        return data


class DashboardNotificationSerializer(serializers.ModelSerializer):
    """Specialized serializer for dashboard views"""
    garden_name = serializers.SerializerMethodField()
    plant_names = serializers.SerializerMethodField()
    next_due = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    instance_id = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'name', 'type', 'interval','type_display', 'subtype', 
                 'garden', 'garden_name', 'plant_names', 'next_due', 
                 'status', 'is_overdue', 'instance_id']
    
    def get_garden_name(self, obj):
        return obj.garden.name or f"Garden {obj.garden.id}"
    
    def get_plant_names(self, obj):
        plants = obj.plants.all()
        if not plants:
            return []
        return [plant.common_name or plant.scientific_name or f"Plant {plant.id}" 
                for plant in plants[:3]]
    
    def get_next_due(self, obj):
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        return instance.next_due if instance else None
    
    def get_status(self, obj):
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        return instance.status if instance else None
    
    def get_is_overdue(self, obj):
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        return instance.is_overdue if instance else False
    
    def get_instance_id(self, obj):
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        return instance.id if instance else None