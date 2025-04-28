# backend/root/plants/tests/factories.py
import factory
import random
from django.utils import timezone
from django.utils.text import slugify
from factory import fuzzy, Faker
from factory.django import DjangoModelFactory
import json

from plants.models import Plant, PlantChangeRequest
from user_management.tests.factories import UserFactory, AdminFactory

class BasePlantFactory(DjangoModelFactory):
    """
    Base factory for Plant model with common attributes.
    
    This abstract factory defines common attributes for all plant types
    and shouldn't be used directly - use the concrete factories below.
    """
    class Meta:
        model = Plant
        abstract = True
    
    # Required fields with sensible defaults
    scientific_name = factory.Sequence(lambda n: f"Botanicus testplantus {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.scientific_name))
    family = factory.Sequence(lambda n: f"Testaceae {n}")
    genus = factory.LazyAttribute(lambda o: o.scientific_name.split()[0])
    genus_id = factory.Sequence(lambda n: n + 1000)
    rank = "species"
    
    # Common optional fields with realistic values
    common_name = factory.Sequence(lambda n: f"Test Plant {n}")
    status = "accepted"
    water_interval = fuzzy.FuzzyInteger(3, 14)
    
    # Simple JSON fields
    synonyms = factory.LazyFunction(lambda: ["Synonym 1", "Synonym 2"])
    duration = factory.LazyFunction(lambda: ["perennial"])
    edible_part = factory.LazyFunction(lambda: ["fruit", "leaves"])
    flower_color = factory.LazyFunction(lambda: ["green", "yellow"])
    foliage_color = factory.LazyFunction(lambda: ["green"])
    fruit_or_seed_color = factory.LazyFunction(lambda: ["brown"])
    growth_months = factory.LazyFunction(lambda: ["apr", "may", "jun", "jul", "aug"])
    bloom_months = factory.LazyFunction(lambda: ["jun", "jul"])
    fruit_months = factory.LazyFunction(lambda: ["aug", "sep"])
    
    # Timestamps
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def set_custom_attributes(self, create, extracted, **kwargs):
        """Set additional attributes after generation"""
        if not create:
            return
            
        if extracted:
            for key, value in extracted.items():
                setattr(self, key, value)


class APIPlantFactory(BasePlantFactory):
    """
    Factory for plants sourced from external API (like Trefle).
    
    Examples:
        # Create basic API plant
        plant = APIPlantFactory()
        
        # Create API plant with specific attributes
        plant = APIPlantFactory(common_name='Specific Plant', water_interval=7)
    """
    api_id = factory.Sequence(lambda n: n + 999999) # raised value
    is_user_created = False
    is_verified = True
    
    # Example data for API plants
    image_url = factory.Sequence(lambda n: f"https://example.com/images/plant{n}.jpg")
    family_common_name = factory.Sequence(lambda n: f"Test Family {n}")
    vegetable = fuzzy.FuzzyChoice([True, False])
    edible = fuzzy.FuzzyChoice([True, False])
    
    detailed_description = Faker('paragraph', nb_sentences=4)
    care_instructions = Faker('paragraph', nb_sentences=3)
    sunlight_requirements = fuzzy.FuzzyChoice(['Full Sun', 'Partial Shade', 'Shade'])
    soil_type = fuzzy.FuzzyChoice(['Loam', 'Clay', 'Sandy', 'Silt'])
    
    # Numeric values
    min_temperature = fuzzy.FuzzyInteger(-5, 10)
    max_temperature = fuzzy.FuzzyInteger(20, 40)
    ph_minimum = fuzzy.FuzzyDecimal(4.5, 6.5)
    ph_maximum = fuzzy.FuzzyDecimal(7.0, 8.5)
    light = fuzzy.FuzzyInteger(4, 10)
    atmospheric_humidity = fuzzy.FuzzyInteger(3, 8)
    average_height = fuzzy.FuzzyInteger(30, 200)
    maximum_height = factory.LazyAttribute(lambda o: o.average_height + random.randint(10, 50))


class UserCreatedPlantFactory(BasePlantFactory):
    """
    Factory for plants created by regular users.
    
    Examples:
        # Create basic user plant with auto-created user
        plant = UserCreatedPlantFactory()
        
        # Create user plant with specific user
        user = UserFactory()
        plant = UserCreatedPlantFactory(created_by=user)
    """
    is_user_created = True
    is_verified = False
    created_by = factory.SubFactory(UserFactory)
    
    # Simplified scientific naming for user plants
    scientific_name = factory.LazyAttribute(lambda o: f"User Plant: {o.common_name}")
    genus = "UserPlantus"
    genus_id = factory.Sequence(lambda n: 10000000 + n)
    family = "User Plants"
    
    # Required fields for user plants
    common_name = factory.Sequence(lambda n: f"My Plant {n}")
    water_interval = fuzzy.FuzzyInteger(3, 10)
    
    # Commonly filled optional fields
    sunlight_requirements = fuzzy.FuzzyChoice(['Full Sun', 'Partial Shade', 'Shade'])
    soil_type = fuzzy.FuzzyChoice(['Any', 'Well-draining', 'Moist'])
    care_instructions = Faker('paragraph', nb_sentences=2)


class VerifiedUserPlantFactory(UserCreatedPlantFactory):
    """Factory for user-created plants that have been verified by admins."""
    is_verified = True
    

class PlantWithFullDetailsFactory(APIPlantFactory):
    """
    Factory for plants with complete details for comprehensive tests.
    
    This creates plants with all possible fields filled in for testing
    detailed views, exports, and comprehensive operations.
    """
    # All basic fields are inherited from APIPlantFactory
    
    # Additional detailed fields
    fertilizing_interval = fuzzy.FuzzyInteger(14, 60)
    pruning_interval = fuzzy.FuzzyInteger(30, 180)
    nutrient_requirements = Faker('paragraph', nb_sentences=2)
    maintenance_notes = Faker('paragraph', nb_sentences=2)
    
    foliage_texture = fuzzy.FuzzyChoice(['Fine', 'Medium', 'Coarse'])
    foliage_retention = fuzzy.FuzzyChoice([True, False])
    fruit_or_seed_conspicuous = fuzzy.FuzzyChoice([True, False])
    fruit_or_seed_shape = fuzzy.FuzzyChoice(['Round', 'Oval', 'Elongated'])
    fruit_or_seed_persistence = fuzzy.FuzzyChoice([True, False])
    
    # Additional measurements
    row_spacing_cm = fuzzy.FuzzyDecimal(10, 100)
    spread_cm = fuzzy.FuzzyDecimal(20, 150)
    days_to_harvest = fuzzy.FuzzyDecimal(60, 200)
    
    sowing = Faker('paragraph', nb_sentences=1)
    minimum_precipitation = fuzzy.FuzzyInteger(300, 800)
    maximum_precipitation = factory.LazyAttribute(lambda o: o.minimum_precipitation + random.randint(200, 1000))
    minimum_root_depth = fuzzy.FuzzyInteger(10, 50)
    growth_rate = fuzzy.FuzzyChoice(['Slow', 'Moderate', 'Rapid'])
    toxicity = fuzzy.FuzzyChoice(['None', 'Low', 'Medium', 'High'])


class PlantChangeRequestFactory(DjangoModelFactory):
    """
    Factory for PlantChangeRequest model.
    
    Examples:
        # Create a change request for a random plant field
        change = PlantChangeRequestFactory()
        
        # Create a change request for a specific field
        plant = APIPlantFactory()
        user = UserFactory()
        change = PlantChangeRequestFactory(
            plant=plant,
            user=user,
            field_name='water_interval',
            old_value='7',
            new_value='5'
        )
    """
    class Meta:
        model = PlantChangeRequest
    
    plant = factory.SubFactory(APIPlantFactory)
    user = factory.SubFactory(UserFactory)
    field_name = factory.LazyFunction(lambda: random.choice(Plant.USER_EDITABLE_FIELDS))
    old_value = "Original value"
    new_value = "Updated value"
    status = "PENDING"
    reason = Faker('sentence')
    
    @factory.post_generation
    def approved(self, create, extracted, **kwargs):
        """Set the change request as approved by admin"""
        if not create or extracted is not True:
            return
            
        self.status = "APPROVED"
        self.reviewer = AdminFactory()
        self.save()
    
    @factory.post_generation
    def rejected(self, create, extracted, **kwargs):
        """Set the change request as rejected by admin"""
        if not create or extracted is not True:
            return
            
        self.status = "REJECTED"
        self.reviewer = AdminFactory()
        self.review_notes = "This change was rejected in testing"
        self.save()


# Factory helpers
def create_plant_test_set():
    """
    Create a test set with different types of plants.
    
    Returns:
        tuple: (api_plant, user_plant, verified_plant, detailed_plant)
    """
    api_plant = APIPlantFactory()
    user_plant = UserCreatedPlantFactory()
    verified_plant = VerifiedUserPlantFactory()
    detailed_plant = PlantWithFullDetailsFactory()
    
    return api_plant, user_plant, verified_plant, detailed_plant