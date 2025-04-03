# backend/root/djangoProject1/urls.py

from django.urls import path, include
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('users/', include(('user_management.urls', 'user_management'), namespace='user_management')),
    path('accounts/', include('allauth.urls')),
    path('select2/', include(('django_select2.urls', 'django_select2'), namespace='django_select2')),
    path('api/v1/', include('plants.api.urls')),
]
