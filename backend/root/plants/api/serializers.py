# backend/root/plants/api/serializers.py

from rest_framework import serializers

class PlantSerializer(serializers.Serializer):
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
    # We'll expose a simplified links dictionary.
    links = serializers.DictField(child=serializers.CharField(), required=False)

class PlantListResponseSerializer(serializers.Serializer):
    data = PlantSerializer(many=True)
    links = serializers.DictField(child=serializers.CharField(), required=False)
    meta = serializers.DictField(child=serializers.IntegerField(), required=False)
