# core/serializers.py
from rest_framework import serializers
from user_management.models import Plants

class PlantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plants
        fields = '__all__'
