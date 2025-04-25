# backend/root/conftest.py
import pytest
from django.test import Client
from pytest_factoryboy import register
from user_management.tests.factories import UserFactory, AdminFactory
from gardens.tests.factories import GardenFactory
from plants.tests.factories import PlantFactory


# Register factories
register(UserFactory)
register(AdminFactory)
register(GardenFactory)
register(PlantFactory)

@pytest.fixture
def client():
    """A Django test client instance"""
    return Client()

@pytest.fixture
def admin_user(django_user_model):
    """Create and return an admin user"""
    return django_user_model.objects.create_superuser(
        email="admin@example.com",
        username="admin",
        password="password123"
    )

@pytest.fixture
def regular_user(django_user_model):
    """Create and return a regular user"""
    return django_user_model.objects.create_user(
        email="user@example.com",
        username="user",
        password="password123"
    )

@pytest.fixture
def authenticated_client(client, regular_user):
    """A logged-in client"""
    client.force_login(regular_user)
    return client