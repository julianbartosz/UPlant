# backend/root/notifications/tests/test_notifications.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from notifications.models import (
    Notification, NotifTypes, NotificationInstance,
    NotificationPlantAssociation
)
from gardens.models import Garden, GardenLog
from plants.models import Plant


class NotificationModelTest(TestCase):
    def setUp(self):
        self.garden = Garden.objects.create(name="My Garden")
        self.plant = Plant.objects.create(name="Tomato", days_to_harvest=60)

    def test_notification_str(self):
        notification = Notification.objects.create(
            garden=self.garden,
            name="Water Tomatoes",
            type=NotifTypes.WA,
            interval=3
        )
        self.assertIn("Water Tomatoes", str(notification))

    def test_invalid_subtype_standard_type(self):
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                garden=self.garden,
                name="Water",
                type=NotifTypes.WA,
                interval=3,
                subtype="Morning"
            )

    def test_missing_subtype_other_type(self):
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                garden=self.garden,
                name="Misc",
                type=NotifTypes.OT,
                interval=3
            )

    def test_valid_other_type_with_subtype(self):
        notif = Notification.objects.create(
            garden=self.garden,
            name="Misc",
            type=NotifTypes.OT,
            interval=3,
            subtype="Fog Alert"
        )
        self.assertEqual(notif.subtype, "Fog Alert")


class NotificationPlantAssociationTest(TestCase):
    def setUp(self):
        self.garden = Garden.objects.create(name="My Garden")
        self.plant = Plant.objects.create(name="Basil")
        self.notification = Notification.objects.create(
            garden=self.garden,
            name="Prune Basil",
            type=NotifTypes.PR,
            interval=7
        )

    def test_unique_association_constraint(self):
        NotificationPlantAssociation.objects.create(
            notification=self.notification,
            plant=self.plant
        )
        with self.assertRaises(ValidationError):
            assoc = NotificationPlantAssociation(
                notification=self.notification,
                plant=self.plant
            )
            assoc.clean()


class NotificationInstanceTest(TestCase):
    def setUp(self):
        self.garden = Garden.objects.create(name="Test Garden")
        self.plant = Plant.objects.create(name="Zucchini", days_to_harvest=40)
        self.notification = Notification.objects.create(
            garden=self.garden,
            name="Harvest Zucchini",
            type=NotifTypes.HA,
            interval=10
        )
        NotificationPlantAssociation.objects.create(notification=self.notification, plant=self.plant)
        self.instance = NotificationInstance.objects.create(
            notification=self.notification,
            next_due=timezone.now() - timedelta(days=1)
        )

    def test_is_overdue(self):
        self.assertTrue(self.instance.is_overdue)

    def test_complete_task(self):
        self.instance.complete_task()
        self.assertEqual(self.instance.status, 'COMPLETED')

    def test_skip_task(self):
        self.instance.skip_task()
        self.assertEqual(self.instance.status, 'SKIPPED')

    def test_str(self):
        self.assertIn(self.notification.name, str(self.instance))

    def test_get_active_notifications(self):
        self.assertIn(self.instance, NotificationInstance.get_active_notifications())

    def test_auto_process_old_notifications(self):
        result = NotificationInstance.auto_process_old_notifications(days_threshold=0)
        self.assertGreater(result['processed'], 0)

    def test_is_harvest_ready_false(self):
        # No GardenLog = not ready
        self.assertFalse(self.instance.is_harvest_ready())

    def test_is_harvest_ready_true(self):
        planted_date = timezone.now().date() - timedelta(days=45)
        GardenLog.objects.create(garden=self.garden, plant=self.plant, planted_date=planted_date)
        self.assertTrue(self.instance.is_harvest_ready())