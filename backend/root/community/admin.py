# backend/root/community/admin.py

from django.contrib import admin
from community.models import Forums, Replies, Likes

admin.site.register(Forums)
admin.site.register(Replies)
admin.site.register(Likes)