from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from core.forms import CustomAuthenticationForm


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(
        template_name='core/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('search_select/', views.search_select, name='search_select'),
]
