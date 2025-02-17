from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms
from user_management.models import User
from django.contrib import admin
from django.contrib.auth.models import Group

from .models import User, Plants, Gardens, Garden_log, Forums, Replies, Likes

admin.site.register(User)
admin.site.unregister(Group)
admin.site.register(Plants)
admin.site.register(Gardens)
admin.site.register(Garden_log)
admin.site.register(Forums)
admin.site.register(Replies)
admin.site.register(Likes)
