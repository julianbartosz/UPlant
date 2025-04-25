# backend/root/plants/tests/test_plants.py

from django.test import TestCase
from django.contrib.auth.models import User
from plants.models import Plant
from plants.forms import PlantForm

class PlantModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.plant = Plant.objects.create(
            name='Tomato',
            description='A red juicy fruit.',
            user=self.user,
            type='Vegetable',
            watering_frequency='Daily',
            sunlight='Full Sun',
            soil_type='Loamy',
            growth_stage='Seedling',
            is_public=True,
        )

    def test_plant_creation(self):
        self.assertEqual(self.plant.name, 'Tomato')
        self.assertEqual(self.plant.user.username, 'testuser')
        self.assertTrue(self.plant.is_public)

    def test_plant_str(self):
        self.assertEqual(str(self.plant), 'Tomato')

class PlantFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='formuser', password='formpass')

    def test_valid_form(self):
        data = {
            'name': 'Cucumber',
            'description': 'A green veggie.',
            'type': 'Vegetable',
            'watering_frequency': 'Weekly',
            'sunlight': 'Partial Sun',
            'soil_type': 'Sandy',
            'growth_stage': 'Mature',
            'is_public': False,
        }
        form = PlantForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        data = {
            'description': 'Missing name field',
            'type': 'Vegetable',
        }
        form = PlantForm(data)
        self.assertFalse(form.is_valid())
