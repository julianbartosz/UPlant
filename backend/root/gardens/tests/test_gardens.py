# backend/root/gardens/tests/test_gardens.py

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from user_management.models import User
from plants.models import Plant
from gardens.models import Garden, GardenLog, PlantHealthStatus
from datetime import timedelta

class GardenModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.plant = Plant.objects.create(common_name='Tomato')
        self.garden = Garden.objects.create(
            user=self.user,
            name='Test Garden',
            description='Test garden description',
            size_x=5,
            size_y=5,
            location='Backyard',
            garden_type='Vegetable'
        )

    def test_garden_creation(self):
        self.assertEqual(self.garden.total_plots(), 25)
        self.assertEqual(self.garden.occupied_plots(), 0)
        self.assertEqual(self.garden.available_plots(), 25)

    def test_plot_availability(self):
        log = GardenLog.objects.create(
            garden=self.garden,
            plant=self.plant,
            x_coordinate=2,
            y_coordinate=2
        )
        self.assertFalse(self.garden.is_plot_available(2, 2))
        self.assertTrue(self.garden.is_plot_available(1, 1))

    def test_get_plant_counts(self):
        GardenLog.objects.create(garden=self.garden, plant=self.plant, x_coordinate=0, y_coordinate=0)
        GardenLog.objects.create(garden=self.garden, plant=self.plant, x_coordinate=1, y_coordinate=0)
        counts = self.garden.get_plant_counts()
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0]['count'], 2)
        self.assertEqual(counts[0]['plant__common_name'], 'Tomato')

    def test_get_recent_activity(self):
        old_log = GardenLog.objects.create(
            garden=self.garden,
            plant=self.plant,
            x_coordinate=0,
            y_coordinate=1,
            planted_date=timezone.now().date() - timedelta(days=31)
        )
        recent_log = GardenLog.objects.create(
            garden=self.garden,
            plant=self.plant,
            x_coordinate=1,
            y_coordinate=1,
            planted_date=timezone.now().date()
        )
        recent = self.garden.get_recent_activity()
        self.assertIn(recent_log, recent)
        self.assertNotIn(old_log, recent)

class GardenLogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loguser', password='testpass')
        self.plant = Plant.objects.create(common_name='Lettuce')
        self.garden = Garden.objects.create(user=self.user, size_x=3, size_y=3)
        self.log = GardenLog.objects.create(
            garden=self.garden,
            plant=self.plant,
            x_coordinate=1,
            y_coordinate=1
        )

    def test_log_string_representation(self):
        self.assertIn('Garden', str(self.log))
        self.assertIn('Lettuce', str(self.log))
        self.assertIn('[1, 1]', str(self.log))

    def test_log_position_bounds(self):
        self.assertTrue(self.log.is_in_bounds())

        out_of_bounds_log = GardenLog(
            garden=self.garden,
            plant=self.plant,
            x_coordinate=5,
            y_coordinate=5
        )
        self.assertFalse(out_of_bounds_log.is_in_bounds())

    def test_record_watering(self):
        self.assertIsNone(self.log.last_watered)
        self.log.record_watering()
        self.assertIsNotNone(self.log.last_watered)

    def test_record_fertilizing(self):
        self.assertIsNone(self.log.last_fertilized)
        self.log.record_fertilizing()
        self.assertIsNotNone(self.log.last_fertilized)

    def test_record_pruning(self):
        self.assertIsNone(self.log.last_pruned)
        self.log.record_pruning()
        self.assertIsNotNone(self.log.last_pruned)

    def test_days_since_watered(self):
        self.assertIsNone(self.log.days_since_watered())
        self.log.record_watering()
        self.assertEqual(self.log.days_since_watered(), 0)

    def test_days_since_planted(self):
        days = self.log.days_since_planted()
        self.assertTrue(isinstance(days, int))
        self.assertEqual(days, 0)

    def test_unique_log_position(self):
        with self.assertRaises(Exception):
            GardenLog.objects.create(
                garden=self.garden,
                plant=self.plant,
                x_coordinate=1,
                y_coordinate=1
            )

    def test_soft_delete_flag(self):
        self.assertFalse(self.log.is_deleted)
        self.log.is_deleted = True
        self.log.save()
        self.assertTrue(GardenLog.objects.get(id=self.log.id).is_deleted)

    def test_garden_soft_delete_flag(self):
        self.assertFalse(self.garden.is_deleted)
        self.garden.is_deleted = True
        self.garden.save()
        self.assertTrue(Garden.objects.get(id=self.garden.id).is_deleted)
