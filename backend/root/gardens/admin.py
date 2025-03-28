# backend/root/gardens/admin.py

from django.contrib import admin
from gardens.models import Gardens, Garden_log

admin.site.register(Gardens)
admin.site.register(Garden_log)