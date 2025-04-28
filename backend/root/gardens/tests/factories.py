# backend/root/gardens/tests/factories.py
import factory
import pytz
import random
from datetime import datetime, timedelta
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory import fuzzy, Faker, SubFactory, LazyAttribute, post_generation

from gardens.models import Garden, GardenLog, PlantHealthStatus
from user_management.tests.factories import UserFactory
from plants.tests.factories import APIPlantFactory, UserCreatedPlantFactory

class GardenFactory(DjangoModelFactory):
    """
    Base factory for Garden model.
    
    Creates gardens with reasonable defaults for basic testing.
    """
    class Meta:
        model = Garden
        skip_postgeneration_save = True
    
    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Test Garden {n}")
    description = factory.Faker('paragraph', nb_sentences=2)
    size_x = fuzzy.FuzzyInteger(5, 20)
    size_y = fuzzy.FuzzyInteger(5, 20)
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    is_deleted = False
    is_public = False
    location = factory.fuzzy.FuzzyChoice(['Backyard', 'Front Yard', 'Balcony', 'Rooftop', 'Indoor'])
    garden_type = factory.fuzzy.FuzzyChoice(['Vegetable', 'Herb', 'Flower', 'Mixed', None])
    
    @factory.post_generation
    def with_plants(self, create, extracted, **kwargs):
        """
        Add plants to the garden.
        
        Args:
            extracted: Number of plants to add, or None for no plants
        
        Examples:
            garden = GardenFactory(with_plants=5)  # Creates 5 garden logs
        """
        if not create or not extracted:
            return
            
        # Add the specified number of plants
        num_plants = extracted if isinstance(extracted, int) else 3
        garden_size = self.size_x * self.size_y
        
        # Don't try to add more plants than the garden can hold
        num_plants = min(num_plants, garden_size)
        
        # Generate unique coordinates
        coordinates = set()
        while len(coordinates) < num_plants:
            x = random.randint(0, self.size_x - 1)
            y = random.randint(0, self.size_y - 1)
            coordinates.add((x, y))
        
        # Create garden logs at those coordinates
        for x, y in coordinates:
            GardenLogFactory(
                garden=self,
                x_coordinate=x,
                y_coordinate=y
            )


class SmallGardenFactory(GardenFactory):
    """Factory for small gardens (5x5)."""
    size_x = 5
    size_y = 5


class LargeGardenFactory(GardenFactory):
    """Factory for large gardens (20x20)."""
    size_x = 20
    size_y = 20


class PublicGardenFactory(GardenFactory):
    """Factory for public gardens visible to all users."""
    is_public = True
    name = factory.Sequence(lambda n: f"Public Garden {n}")
    description = "This garden is visible to everyone"


class DeletedGardenFactory(GardenFactory):
    """Factory for soft-deleted gardens."""
    is_deleted = True
    name = factory.Sequence(lambda n: f"Deleted Garden {n}")


class SpecificGardenFactory(GardenFactory):
    """
    Factory for gardens with specific dimensions.
    
    Examples:
        garden = SpecificGardenFactory(size_x=10, size_y=15)
    """
    class Meta:
        model = Garden
        exclude = ('_size',)
        skip_postgeneration_save = True
        
    _size = factory.LazyAttribute(lambda o: (10, 10))  # Default size
    size_x = factory.LazyAttribute(lambda o: o._size[0])
    size_y = factory.LazyAttribute(lambda o: o._size[1])
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to allow specifying size_x and size_y together."""
        if 'size_x' in kwargs and 'size_y' in kwargs:
            kwargs['_size'] = (kwargs['size_x'], kwargs['size_y'])
        return super()._create(model_class, *args, **kwargs)


class GardenLogFactory(DjangoModelFactory):
    """
    Base factory for GardenLog model.
    
    Creates garden logs with reasonable defaults.
    """
    class Meta:
        model = GardenLog
        skip_postgeneration_save = True
    
    garden = factory.SubFactory(GardenFactory)
    plant = factory.SubFactory(APIPlantFactory)
    planted_date = factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=random.randint(1, 60)))
    x_coordinate = factory.Sequence(lambda n: n % 10)  # Ensure within bounds for most gardens
    y_coordinate = factory.LazyAttribute(lambda o: o.x_coordinate % 10)  # Ensure within bounds
    health_status = factory.fuzzy.FuzzyChoice([status.value for status in PlantHealthStatus])
    notes = factory.Faker('paragraph', nb_sentences=1)
    last_watered = factory.LazyFunction(lambda: timezone.now() - timedelta(days=random.randint(0, 7)))
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    is_deleted = False
    
    @factory.post_generation
    def ensure_coordinates_in_bounds(self, create, extracted, **kwargs):
        """Ensure coordinates are within garden bounds."""
        if not create:
            return
            
        # Adjust coordinates to fit within garden bounds
        if hasattr(self, 'garden') and self.garden:
            self.x_coordinate = min(self.x_coordinate, self.garden.size_x - 1)
            self.y_coordinate = min(self.y_coordinate, self.garden.size_y - 1)
            self.save()


class HealthyPlantLogFactory(GardenLogFactory):
    """Factory for garden logs with healthy plants."""
    health_status = PlantHealthStatus.HEALTHY
    last_watered = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))
    last_fertilized = factory.LazyFunction(lambda: timezone.now() - timedelta(days=14))


class UnhealthyPlantLogFactory(GardenLogFactory):
    """Factory for garden logs with unhealthy plants."""
    health_status = PlantHealthStatus.POOR
    last_watered = factory.LazyFunction(lambda: timezone.now() - timedelta(days=14))
    notes = "Plant appears to be struggling due to lack of water"


class DeadPlantLogFactory(GardenLogFactory):
    """Factory for garden logs with dead plants."""
    health_status = PlantHealthStatus.DEAD
    last_watered = factory.LazyFunction(lambda: timezone.now() - timedelta(days=30))
    notes = "Plant has died"


class NewlyPlantedLogFactory(GardenLogFactory):
    """Factory for recently planted garden logs."""
    planted_date = factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=2))
    health_status = PlantHealthStatus.HEALTHY
    last_watered = factory.LazyFunction(timezone.now)
    growth_stage = "Seedling"


class MaturePlantLogFactory(GardenLogFactory):
    """Factory for mature plants that were planted a while ago."""
    planted_date = factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=120))
    health_status = PlantHealthStatus.EXCELLENT
    last_watered = factory.LazyFunction(lambda: timezone.now() - timedelta(days=2))
    last_fertilized = factory.LazyFunction(lambda: timezone.now() - timedelta(days=14))
    last_pruned = factory.LazyFunction(lambda: timezone.now() - timedelta(days=21))
    growth_stage = "Mature"


class UserPlantInGardenFactory(GardenLogFactory):
    """Factory for garden logs with user-created plants rather than API plants."""
    plant = factory.SubFactory(UserCreatedPlantFactory)


# Helper functions
def create_garden_with_diverse_plants(user=None, garden_size=(10, 10), plant_count=5):
    """
    Create a garden with diverse plant health statuses.
    
    Args:
        user: User who owns the garden. If None, a new user is created.
        garden_size: Tuple of (size_x, size_y)
        plant_count: Number of plants to add
    
    Returns:
        Garden instance with plants added
    """
    user = user or UserFactory()
    garden = GardenFactory(
        user=user,
        size_x=garden_size[0],
        size_y=garden_size[1]
    )
    
    # Add plants with different health statuses
    health_factories = [
        HealthyPlantLogFactory,
        UnhealthyPlantLogFactory, 
        DeadPlantLogFactory,
        NewlyPlantedLogFactory,
        MaturePlantLogFactory
    ]
    
    # Generate unique coordinates
    max_plants = min(plant_count, garden.size_x * garden.size_y)
    coordinates = set()
    while len(coordinates) < max_plants:
        x = random.randint(0, garden.size_x - 1)
        y = random.randint(0, garden.size_y - 1)
        coordinates.add((x, y))
    
    # Create logs with different factory types
    for i, (x, y) in enumerate(coordinates):
        factory_class = health_factories[i % len(health_factories)]
        factory_class(
            garden=garden,
            x_coordinate=x,
            y_coordinate=y
        )
    
    return garden


def create_garden_with_watering_needs(user=None, size=(10, 10)):
    """
    Create a garden with plants that need watering soon.
    
    Returns:
        Garden instance with plants that need water
    """
    garden = GardenFactory(
        user=user or UserFactory(),
        size_x=size[0],
        size_y=size[1]
    )
    
    # Add 3 plants with different last_watered times
    GardenLogFactory(
        garden=garden,
        x_coordinate=0,
        y_coordinate=0,
        last_watered=timezone.now() - timedelta(days=10),
        health_status=PlantHealthStatus.FAIR,
        notes="Needs watering urgently"
    )
    
    GardenLogFactory(
        garden=garden,
        x_coordinate=1,
        y_coordinate=1,
        last_watered=timezone.now() - timedelta(days=6),
        health_status=PlantHealthStatus.HEALTHY,
        notes="Will need water soon"
    )
    
    GardenLogFactory(
        garden=garden,
        x_coordinate=2,
        y_coordinate=2,
        last_watered=timezone.now() - timedelta(hours=12),
        health_status=PlantHealthStatus.EXCELLENT,
        notes="Recently watered"
    )
    
    return garden