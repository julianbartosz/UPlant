# backend/root/user_management/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from user_management.models import User, Roles

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True
    role = Roles.US

class AdminFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    username = factory.Sequence(lambda n: f'admin{n}')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True
    role = Roles.AD
    is_superuser = True