# backend/root/gardens/admin.py

from django.contrib import admin
from gardens.models import Garden, GardenLog

admin.site.register(Garden)
admin.site.register(GardenLog)