# backend/root/conftest.py
import pytest
from django.test import Client

@pytest.fixture(scope="session", autouse=True)
def django_db_setup():
    """Initialize Django before any tests are run."""
    import os
    import sys
    import django
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject1.settings")
    django.setup()

@pytest.fixture(scope="session", autouse=True)
def register_factories():
    """Register all factories after Django is initialized."""
    from pytest_factoryboy import register
    
    # User Management Factories
    from user_management.tests.factories import (
        UserFactory, AdminFactory, ModeratorFactory,
        InactiveUserFactory, NewUserFactory, UserWithActivityFactory
    )
    
    # Plant Factories
    from plants.tests.factories import (
        APIPlantFactory, UserCreatedPlantFactory,
        VerifiedUserPlantFactory, PlantWithFullDetailsFactory,
        PlantChangeRequestFactory
    )
    
    # Garden Factories
    from gardens.tests.factories import (
        GardenFactory, SmallGardenFactory, LargeGardenFactory,
        PublicGardenFactory, DeletedGardenFactory, GardenLogFactory,
        HealthyPlantLogFactory, UnhealthyPlantLogFactory,
        DeadPlantLogFactory, NewlyPlantedLogFactory,
        MaturePlantLogFactory, UserPlantInGardenFactory
    )
    
    # Notification Factories
    from notifications.tests.factories import (
        NotificationFactory, WaterNotificationFactory,
        FertilizeNotificationFactory, PruneNotificationFactory,
        HarvestNotificationFactory, WeatherNotificationFactory,
        OtherNotificationFactory, NotificationPlantAssociationFactory,
        NotificationInstanceFactory, OverdueNotificationInstanceFactory,
        CompletedNotificationInstanceFactory, SkippedNotificationInstanceFactory,
        MissedNotificationInstanceFactory
    )
    
    # Register all factories
    # User Management
    register(UserFactory)
    register(AdminFactory)
    register(ModeratorFactory)
    register(InactiveUserFactory)
    register(NewUserFactory)
    register(UserWithActivityFactory)
    
    # Plants
    register(APIPlantFactory)
    register(UserCreatedPlantFactory)
    register(VerifiedUserPlantFactory)
    register(PlantWithFullDetailsFactory)
    register(PlantChangeRequestFactory)
    
    # Gardens
    register(GardenFactory)
    register(SmallGardenFactory)
    register(LargeGardenFactory)
    register(PublicGardenFactory)
    register(DeletedGardenFactory)
    register(GardenLogFactory)
    register(HealthyPlantLogFactory)
    register(UnhealthyPlantLogFactory)
    register(DeadPlantLogFactory)
    register(NewlyPlantedLogFactory)
    register(MaturePlantLogFactory)
    register(UserPlantInGardenFactory)
    
    # Notifications
    register(NotificationFactory)
    register(WaterNotificationFactory)
    register(FertilizeNotificationFactory)
    register(PruneNotificationFactory)
    register(HarvestNotificationFactory)
    register(WeatherNotificationFactory)
    register(OtherNotificationFactory)
    register(NotificationPlantAssociationFactory)
    register(NotificationInstanceFactory)
    register(OverdueNotificationInstanceFactory)
    register(CompletedNotificationInstanceFactory)
    register(SkippedNotificationInstanceFactory)
    register(MissedNotificationInstanceFactory)

# ==================== Base Client Fixtures ====================

@pytest.fixture
def client():
    """A Django test client instance"""
    return Client()

@pytest.fixture
def api_client():
    """A Django test client for API requests with appropriate headers"""
    client = Client()
    client.defaults['HTTP_ACCEPT'] = 'application/json'
    client.defaults['CONTENT_TYPE'] = 'application/json'
    return client

# ==================== Authentication Fixtures ====================

@pytest.fixture
def admin_user(admin_factory):
    """Create and return an admin user with standard credentials"""
    return admin_factory(
        email="admin@example.com",
        username="admin",
        password="password123"
    )

@pytest.fixture
def moderator_user(moderator_factory):
    """Create and return a moderator user"""
    return moderator_factory(
        email="moderator@example.com",
        username="moderator",
        password="password123"
    )

@pytest.fixture
def regular_user(user_factory):
    """Create and return a regular user with standard credentials"""
    return user_factory(
        email="user@example.com",
        username="user",
        password="password123"
    )

@pytest.fixture
def inactive_user(inactive_user_factory):
    """Create and return an inactive user"""
    return inactive_user_factory(
        email="inactive@example.com",
        username="inactive",
        password="password123"
    )

@pytest.fixture
def authenticated_client(client, regular_user):
    """A client logged in as a regular user"""
    client.force_login(regular_user)
    return client

@pytest.fixture
def admin_client(client, admin_user):
    """A client logged in as an admin user"""
    client.force_login(admin_user)
    return client

@pytest.fixture
def moderator_client(client, moderator_user):
    """A client logged in as a moderator user"""
    client.force_login(moderator_user)
    return client

@pytest.fixture
def authenticated_api_client(api_client, regular_user):
    """An API client logged in as a regular user"""
    api_client.force_login(regular_user)
    return api_client

# ==================== Plant Fixtures ====================

@pytest.fixture
def api_plant(api_plant_factory):
    """Create and return a plant from an external API source"""
    return api_plant_factory()

@pytest.fixture
def user_plant(user_created_plant_factory, regular_user):
    """Create and return a user-created plant"""
    return user_created_plant_factory(created_by=regular_user)

@pytest.fixture
def detailed_plant(plant_with_full_details_factory):
    """Create and return a plant with all details filled in"""
    return plant_with_full_details_factory()

@pytest.fixture
def plants_set():
    """Create a set with one of each plant type"""
    from plants.tests.factories import create_plant_test_set
    return create_plant_test_set()

# ==================== Garden Fixtures ====================

@pytest.fixture
def garden(garden_factory, regular_user):
    """Create and return a garden for the regular user"""
    return garden_factory(user=regular_user)

@pytest.fixture
def public_garden(public_garden_factory):
    """Create and return a public garden"""
    return public_garden_factory()

@pytest.fixture
def garden_with_plants(garden_factory, regular_user):
    """Create a garden with several plants already added"""
    garden = garden_factory(user=regular_user, with_plants=5)
    return garden

@pytest.fixture
def diverse_garden(regular_user):
    """Create a garden with plants in various health states"""
    from gardens.tests.factories import create_garden_with_diverse_plants
    return create_garden_with_diverse_plants(user=regular_user)

@pytest.fixture
def watering_garden(regular_user):
    """Create a garden with plants that need watering"""
    from gardens.tests.factories import create_garden_with_watering_needs
    return create_garden_with_watering_needs(user=regular_user)

# ==================== Notification Fixtures ====================

@pytest.fixture
def water_notification(water_notification_factory, garden, api_plant):
    """Create a water notification for a garden"""
    from notifications.tests.factories import NotificationPlantAssociationFactory
    notification = water_notification_factory(garden=garden)
    NotificationPlantAssociationFactory(notification=notification, plant=api_plant)
    return notification

@pytest.fixture
def notification_due_today(notification_instance_factory, water_notification):
    """Create a notification instance that's due today"""
    from django.utils import timezone
    return notification_instance_factory(
        notification=water_notification,
        next_due=timezone.now(),
        status='PENDING'
    )

@pytest.fixture
def notification_test_set(garden):
    """Create a comprehensive set of notifications for testing"""
    from notifications.tests.factories import create_notifications_test_set
    return create_notifications_test_set(garden=garden)

# ==================== Combined Fixtures ====================

@pytest.fixture
def complete_user_setup(regular_user):
    """
    Create a complete environment for a user with gardens, plants and notifications.
    
    Returns a dictionary with all created entities.
    """
    # Import inside function to avoid premature import
    from gardens.tests.factories import GardenFactory, HealthyPlantLogFactory, NewlyPlantedLogFactory
    from plants.tests.factories import APIPlantFactory, UserCreatedPlantFactory
    from notifications.tests.factories import (
        WaterNotificationFactory, FertilizeNotificationFactory,
        NotificationPlantAssociationFactory, NotificationInstanceFactory,
        OverdueNotificationInstanceFactory
    )
    
    # Create a garden
    garden = GardenFactory(user=regular_user)
    
    # Create plants and add to garden
    plant1 = APIPlantFactory()
    plant2 = UserCreatedPlantFactory(created_by=regular_user)
    
    garden_log1 = HealthyPlantLogFactory(
        garden=garden, 
        plant=plant1,
        x_coordinate=0,
        y_coordinate=0
    )
    garden_log2 = NewlyPlantedLogFactory(
        garden=garden,
        plant=plant2,
        x_coordinate=1,
        y_coordinate=1
    )
    
    # Create notifications
    water_notification = WaterNotificationFactory(garden=garden)
    NotificationPlantAssociationFactory(notification=water_notification, plant=plant1)
    NotificationPlantAssociationFactory(notification=water_notification, plant=plant2)
    
    fertilize_notification = FertilizeNotificationFactory(garden=garden)
    NotificationPlantAssociationFactory(notification=fertilize_notification, plant=plant1)
    
    # Create notification instances
    water_instance = NotificationInstanceFactory(notification=water_notification)
    overdue_instance = OverdueNotificationInstanceFactory(notification=fertilize_notification)
    
    return {
        'user': regular_user,
        'garden': garden,
        'plants': [plant1, plant2],
        'logs': [garden_log1, garden_log2],
        'notifications': {
            'water': water_notification,
            'fertilize': fertilize_notification,
        },
        'instances': {
            'water': water_instance,
            'overdue': overdue_instance,
        }
    }

# ==================== Test Helpers ====================

@pytest.fixture
def login_user():
    """
    Helper function to log in a user with the client.
    
    Usage: 
        def test_something(client, login_user):
            login_user(client, 'user@example.com', 'password123')
    """
    from django.urls import reverse
    
    def _login_user(client, username, password):
        client.post(
            reverse('login'), 
            {'username': username, 'password': password}
        )
        return client
    
    return _login_user

@pytest.fixture
def assert_requires_login():
    """
    Helper function to assert that a view requires login.
    
    Usage:
        def test_protected_view(client, assert_requires_login):
            assert_requires_login(client, '/protected/url/')
    """
    def _assert_requires_login(client, url, redirect_url=None):
        response = client.get(url)
        assert response.status_code == 302
        if redirect_url:
            assert redirect_url in response.url
        else:
            assert '/login/' in response.url
    
    return _assert_requires_login

@pytest.fixture
def create_image_file():
    """
    Create a test image file for testing file uploads.
    
    Usage:
        def test_upload(client, create_image_file):
            image_file = create_image_file()
            response = client.post('/upload/', {'image': image_file})
    """
    from PIL import Image
    from io import BytesIO
    
    def _create_image_file(filename='test.png', size=(100, 100), color='blue'):
        file = BytesIO()
        image = Image.new('RGB', size=size, color=color)
        image.save(file, 'png')
        file.name = filename
        file.seek(0)
        return file
    
    return _create_image_file