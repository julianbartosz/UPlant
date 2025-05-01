# backend/root/notifications/tests/factories.py
import factory
import random
from datetime import timedelta
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory import fuzzy, Faker, SubFactory

from notifications.models import (
    Notification, 
    NotificationPlantAssociation, 
    NotificationInstance,
    NotifTypes
)
from gardens.tests.factories import GardenFactory
from plants.tests.factories import APIPlantFactory, UserCreatedPlantFactory
from user_management.tests.factories import UserFactory

class NotificationFactory(DjangoModelFactory):
    """
    Base factory for Notification model.
    
    Creates notification settings with reasonable defaults.
    """
    class Meta:
        model = Notification
        skip_postgeneration_save = True
    
    garden = factory.SubFactory(GardenFactory)
    name = factory.Sequence(lambda n: f"Test Notification {n}")
    type = factory.fuzzy.FuzzyChoice([
        NotifTypes.PR, 
        NotifTypes.FE,
        NotifTypes.HA,
        NotifTypes.WA,
        NotifTypes.WE
    ])  # Excluding Other to avoid subtype validation issues by default
    interval = fuzzy.FuzzyInteger(1, 30)
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    
    @factory.post_generation
    def plants(self, create, extracted, **kwargs):
        """
        Add plants to the notification.
        
        Args:
            extracted: List of plants to add, or int for number of random plants
        
        Examples:
            # Create notification with 3 random plants
            notification = NotificationFactory(plants=3)
            
            # Create notification with specific plants
            plants = [APIPlantFactory(), APIPlantFactory()]
            notification = NotificationFactory(plants=plants)
        """
        if not create:
            return
            
        # Handle case where an integer is passed (create that many plants)
        if isinstance(extracted, int):
            for _ in range(extracted):
                NotificationPlantAssociationFactory(notification=self)
        # Handle case where a list of plants is passed
        elif extracted:
            for plant in extracted:
                NotificationPlantAssociationFactory(
                    notification=self,
                    plant=plant
                )


class WaterNotificationFactory(NotificationFactory):
    """Factory for water notifications."""
    type = NotifTypes.WA
    name = factory.Sequence(lambda n: f"Water Plants {n}")
    interval = fuzzy.FuzzyInteger(3, 10)  # More reasonable watering interval


class FertilizeNotificationFactory(NotificationFactory):
    """Factory for fertilize notifications."""
    type = NotifTypes.FE
    name = factory.Sequence(lambda n: f"Fertilize Plants {n}")
    interval = fuzzy.FuzzyInteger(14, 45)  # More reasonable fertilizing interval


class PruneNotificationFactory(NotificationFactory):
    """Factory for pruning notifications."""
    type = NotifTypes.PR
    name = factory.Sequence(lambda n: f"Prune Plants {n}")
    interval = fuzzy.FuzzyInteger(30, 90)  # More reasonable pruning interval


class HarvestNotificationFactory(NotificationFactory):
    """Factory for harvest notifications."""
    type = NotifTypes.HA
    name = factory.Sequence(lambda n: f"Harvest Plants {n}")
    interval = fuzzy.FuzzyInteger(7, 60)  # Reasonable harvest interval


class WeatherNotificationFactory(NotificationFactory):
    """Factory for weather notifications."""
    type = NotifTypes.WE
    name = factory.Sequence(lambda n: f"Weather Alert {n}")
    interval = fuzzy.FuzzyInteger(1, 7)  # More frequent for weather alerts


class OtherNotificationFactory(NotificationFactory):
    """Factory for custom 'Other' notifications with required subtype."""
    type = NotifTypes.OT
    subtype = factory.Sequence(lambda n: f"Custom Type {n}")
    name = factory.LazyAttribute(lambda o: f"{o.subtype} Reminder")


class NotificationPlantAssociationFactory(DjangoModelFactory):
    """
    Factory for NotificationPlantAssociation model.
    
    Creates associations between notifications and plants.
    """
    class Meta:
        model = NotificationPlantAssociation
        skip_postgeneration_save = True
    
    notification = factory.SubFactory(NotificationFactory)
    plant = factory.SubFactory(APIPlantFactory)
    custom_interval = None  # Use notification's default interval
    
    @factory.post_generation
    def with_custom_interval(self, create, extracted, **kwargs):
        """
        Set a custom interval for this specific plant.
        
        Args:
            extracted: Custom interval value, or True to generate a random one
        """
        if not create:
            return
            
        if extracted is True:
            # Generate a random custom interval that's different from the notification's default
            base_interval = self.notification.interval
            self.custom_interval = base_interval + random.randint(-2, 5)
            # Ensure it's at least 1 day
            self.custom_interval = max(1, self.custom_interval)
            self.save()
        elif extracted and isinstance(extracted, int):
            self.custom_interval = extracted
            self.save()


class NotificationInstanceFactory(DjangoModelFactory):
    """
    Factory for NotificationInstance model.
    
    Creates instances of notifications that represent actual tasks.
    """
    class Meta:
        model = NotificationInstance
        skip_postgeneration_save = True
    
    notification = factory.SubFactory(NotificationFactory)
    next_due = factory.LazyFunction(lambda: timezone.now() + timedelta(days=random.randint(1, 5)))
    last_completed = None  # Default to not completed before
    message = factory.Faker('sentence')
    status = 'PENDING'
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    completed_at = None
    
    @factory.post_generation
    def completed(self, create, extracted, **kwargs):
        """
        Mark the notification as completed.
        
        Args:
            extracted: If True, mark as completed
        """
        if not create or not extracted:
            return
            
        completed_time = timezone.now() - timedelta(days=random.randint(1, 10))
        self.status = 'COMPLETED'
        self.last_completed = completed_time
        self.completed_at = completed_time
        self.next_due = completed_time + timedelta(days=self.notification.interval)
        self.save()
    
    @factory.post_generation
    def skipped(self, create, extracted, **kwargs):
        """Mark the notification as skipped."""
        if not create or not extracted:
            return
            
        skipped_time = timezone.now() - timedelta(days=random.randint(1, 5))
        self.status = 'SKIPPED'
        self.updated_at = skipped_time
        self.next_due = skipped_time + timedelta(days=self.notification.interval)
        self.save()


class OverdueNotificationInstanceFactory(NotificationInstanceFactory):
    """Factory for overdue notification instances."""
    next_due = factory.LazyFunction(lambda: timezone.now() - timedelta(days=random.randint(1, 10)))
    status = 'PENDING'


class CompletedNotificationInstanceFactory(NotificationInstanceFactory):
    """Factory for completed notification instances."""
    status = 'COMPLETED'
    last_completed = factory.LazyFunction(lambda: timezone.now() - timedelta(days=random.randint(1, 10)))
    completed_at = factory.LazyAttribute(lambda o: o.last_completed)
    next_due = factory.LazyAttribute(lambda o: o.last_completed + timedelta(days=o.notification.interval))


class SkippedNotificationInstanceFactory(NotificationInstanceFactory):
    """Factory for skipped notification instances."""
    status = 'SKIPPED'
    next_due = factory.LazyFunction(lambda: timezone.now() + timedelta(days=random.randint(1, 10)))


class MissedNotificationInstanceFactory(NotificationInstanceFactory):
    """Factory for missed notification instances."""
    status = 'MISSED'
    next_due = factory.LazyFunction(lambda: timezone.now() - timedelta(days=random.randint(15, 30)))


# Helper functions
def create_notifications_test_set(garden=None, user=None):
    """
    Create a comprehensive set of notifications for testing.
    
    Args:
        garden: Garden to attach notifications to, or None to create one
        user: User who owns the garden, or None to create one
    
    Returns:
        dict: Dictionary containing all created objects
    """
    # Create user and garden if not provided
    user = user or UserFactory()
    garden = garden or GardenFactory(user=user)
    
    # Create plants
    plants = [APIPlantFactory() for _ in range(5)]
    
    # Create one of each notification type
    water_notif = WaterNotificationFactory(garden=garden)
    fertilize_notif = FertilizeNotificationFactory(garden=garden)
    prune_notif = PruneNotificationFactory(garden=garden)
    harvest_notif = HarvestNotificationFactory(garden=garden)
    weather_notif = WeatherNotificationFactory(garden=garden)
    other_notif = OtherNotificationFactory(garden=garden)
    
    # Associate plants with notifications
    for plant in plants:
        NotificationPlantAssociationFactory(notification=water_notif, plant=plant)
        NotificationPlantAssociationFactory(notification=fertilize_notif, plant=plant)
        NotificationPlantAssociationFactory(notification=prune_notif, plant=plant)
        NotificationPlantAssociationFactory(notification=harvest_notif, plant=plant)
    
    # Create instances in various states
    water_instances = [
        NotificationInstanceFactory(notification=water_notif),  # Pending
        OverdueNotificationInstanceFactory(notification=water_notif),  # Overdue
        CompletedNotificationInstanceFactory(notification=water_notif),  # Completed
    ]
    
    fertilize_instances = [
        NotificationInstanceFactory(notification=fertilize_notif),  # Pending
        SkippedNotificationInstanceFactory(notification=fertilize_notif),  # Skipped
    ]
    
    prune_instances = [
        NotificationInstanceFactory(notification=prune_notif),  # Pending
    ]
    
    harvest_instances = [
        NotificationInstanceFactory(notification=harvest_notif),  # Pending
        MissedNotificationInstanceFactory(notification=harvest_notif),  # Missed
    ]
    
    weather_instances = [
        NotificationInstanceFactory(notification=weather_notif),  # Pending
    ]
    
    other_instances = [
        NotificationInstanceFactory(notification=other_notif),  # Pending
    ]
    
    # Return all created objects
    return {
        'user': user,
        'garden': garden,
        'plants': plants,
        'notifications': {
            'water': water_notif,
            'fertilize': fertilize_notif,
            'prune': prune_notif,
            'harvest': harvest_notif,
            'weather': weather_notif,
            'other': other_notif,
        },
        'instances': {
            'water': water_instances,
            'fertilize': fertilize_instances,
            'prune': prune_instances,
            'harvest': harvest_instances,
            'weather': weather_instances,
            'other': other_instances,
        }
    }


def create_notification_sequence(notification_type, count=5, days_span=30, garden=None):
    """
    Create a sequence of notification instances over time.
    
    Useful for testing notification history and patterns.
    
    Args:
        notification_type: Type from NotifTypes enum
        count: Number of instances to create
        days_span: Time span in days to spread instances over
        garden: Garden to attach to, or None to create one
    
    Returns:
        tuple: (notification, list of instances)
    """
    # Create garden if not provided
    garden = garden or GardenFactory()
    
    # Create notification based on type
    factory_map = {
        NotifTypes.WA: WaterNotificationFactory,
        NotifTypes.FE: FertilizeNotificationFactory,
        NotifTypes.PR: PruneNotificationFactory,
        NotifTypes.HA: HarvestNotificationFactory,
        NotifTypes.WE: WeatherNotificationFactory,
        NotifTypes.OT: OtherNotificationFactory,
    }
    
    notification_factory = factory_map.get(notification_type, NotificationFactory)
    notification = notification_factory(
        garden=garden, 
        type=notification_type,
        interval=max(1, int(days_span / count))
    )
    
    # Create plants and associate with notification
    plants = [APIPlantFactory() for _ in range(2)]
    for plant in plants:
        NotificationPlantAssociationFactory(notification=notification, plant=plant)
    
    # Create instances distributed over the time span
    instances = []
    now = timezone.now()
    
    for i in range(count):
        # Calculate days in the past for this instance
        days_ago = days_span * (1 - (i / count))
        instance_date = now - timedelta(days=days_ago)
        
        # Earlier instances are completed, later ones pending
        if i < count * 0.7:  # 70% completed
            instance = CompletedNotificationInstanceFactory(
                notification=notification,
                last_completed=instance_date,
                completed_at=instance_date,
                next_due=instance_date + timedelta(days=notification.interval)
            )
        else:
            # The last 30% are pending
            instance = NotificationInstanceFactory(
                notification=notification,
                next_due=instance_date + timedelta(days=notification.interval)
            )
            
        instances.append(instance)
    
    return notification, instances