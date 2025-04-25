# backend/root/user_management/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user_management.api.views import LoginView

from user_management.api.views import (
    # User account endpoints
    UserDetailView, UserProfileView,
    
    # Password management
    PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView,
    
    # Email management
    EmailVerificationView, ResendVerificationEmailView, EmailChangeRequestView,
    SetPrimaryEmailView,
    
    # Social account management
    SocialAccountDisconnectView,
    
    # Admin endpoints
    AdminUserViewSet,

    # Weather endpoints
    UserWeatherView, UserLocationUpdateView,
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')

# URL patterns for API endpoints
urlpatterns = [
    # User profile endpoints
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('me/profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Weather endpoints
    path('me/profile/weather/', UserWeatherView.as_view(), name='user-weather'),
    path('me/profile/update_location/', UserLocationUpdateView.as_view(), name='user-update-location'),
    
    # Password management endpoints
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Email management endpoints
    path('email/verify/<str:key>/', EmailVerificationView.as_view(), name='email-verification'),
    path('email/resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('email/change/', EmailChangeRequestView.as_view(), name='email-change'),
    path('email/set-primary/', SetPrimaryEmailView.as_view(), name='set-primary-email'),
    
    # Social account endpoints
    path('social/disconnect/', SocialAccountDisconnectView.as_view(), name='disconnect-social'),
    
    # Include router URLs for ViewSets
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='api-token-auth'),
]

# Named URL patterns for this app
app_name = 'user_api'