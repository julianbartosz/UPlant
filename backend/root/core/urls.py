# backend/root/core/urls.py

from django.urls import path, include
from core import views
from django.contrib.auth.views import LoginView, LogoutView
from core.views_api import plants_list, api_root
from core.forms import CustomAuthenticationForm

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(
        template_name='core/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('search_select/', views.search_select, name='search_select'),

    # API
    path('api/', api_root, name='api_root'),
    path('api/plants/', plants_list, name='plants_list'),

    # Footer links
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('help/', views.help_page, name='help'),  # Using help_page because help is a Python keyword
    path('terms/', views.terms, name='terms'),
    path('contact/', views.contact, name='contact'),
]
