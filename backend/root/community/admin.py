# backend/root/community/admin.py

from django.contrib import admin
from community.models import Forum, Reply, Like

admin.site.register(Forum)
admin.site.register(Reply)
admin.site.register(Like)