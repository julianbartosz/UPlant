# backend/root/plants/admin.py

from django.contrib import admin
from .models import Plant

admin.site.register(Plant)