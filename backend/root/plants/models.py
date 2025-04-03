# backend/root/plants/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Plant(models.Model):
    # Explicitly define the primary key field (Django would create this anyway)
    id = models.AutoField(primary_key=True)

    # API fields
    api_id = models.IntegerField(
        null=True, blank=True, unique=True, 
        help_text="ID from external API, if available"
    )
    common_name = models.CharField(
        max_length=255, null=True, blank=True, 
        help_text="Common name of the plant (if available)"
    )
    slug = models.SlugField(unique=True, help_text="Unique human-readable identifier")
    scientific_name = models.CharField(max_length=255)

    STATUS_CHOICES = [
        ('accepted', 'Accepted'),
        ('unknown', 'Unknown'),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='unknown',
        help_text="Acceptance status of the plant name"
    )
    
    RANK_CHOICES = [
        ('species', 'Species'),
        ('ssp', 'Subspecies'),
        ('var', 'Variety'),
        ('form', 'Form'),
        ('hybrid', 'Hybrid'),
        ('subvar', 'Subvariety'),
    ]
    rank = models.CharField(
        max_length=20, choices=RANK_CHOICES, 
        help_text="Taxonomic rank of the plant"
    )
    
    family_common_name = models.CharField(
        max_length=255, null=True, blank=True, 
        help_text="Common name of the plant family (if available)"
    )
    family = models.CharField(max_length=255, help_text="Scientific name of the plant family")
    genus_id = models.IntegerField(help_text="ID of the plant genus")
    genus = models.CharField(max_length=255, help_text="Scientific name of the plant genus")
    image_url = models.URLField(null=True, blank=True, help_text="Primary image URL for the plant")
    
    # Store synonyms as a JSON array
    synonyms = models.JSONField(
        null=True, blank=True, 
        help_text="List of synonym names (as a JSON array)"
    )
    
    # Botanical & classification data for catalog filtering
    vegetable = models.BooleanField(
        default=False, 
        help_text="Is the plant classified as a vegetable?"
    )
    duration = models.JSONField(
        null=True, blank=True, 
        help_text="Plant duration(s) (e.g., annual, biennial, perennial)"
    )
    edible = models.BooleanField(
        default=False, 
        help_text="Is the plant edible?"
    )
    edible_part = models.JSONField(
        null=True, blank=True, 
        help_text="Edible parts of the plant (e.g., roots, leaves, fruits)"
    )

    # Flower details
    flower_color = models.JSONField(
        null=True, blank=True, 
        help_text="Flower color(s) (e.g., ['red', 'yellow'])"
    )
    flower_conspicuous = models.BooleanField(
        null=True, default=False, 
        help_text="Are the flowers visually prominent?"
    )
    # Foliage details
    foliage_texture = models.CharField(
        max_length=50, null=True, blank=True, 
        help_text="Texture of the foliage (e.g., fine, medium, coarse)"
    )
    foliage_color = models.JSONField(
        null=True, blank=True, 
        help_text="Foliage color(s) (e.g., ['green', 'grey'])"
    )
    foliage_retention = models.BooleanField(
        null=True, default=False, 
        help_text="Does the plant retain its foliage all year?"
    )
    # Fruit/seed details
    fruit_or_seed_conspicuous = models.BooleanField(
        null=True, default=False, 
        help_text="Are the fruits or seeds visually prominent?"
    )
    fruit_or_seed_color = models.JSONField(
        null=True, blank=True, 
        help_text="Fruit or seed color(s) (e.g., ['red', 'orange'])"
    )
    fruit_or_seed_shape = models.CharField(
        max_length=50, null=True, blank=True, 
        help_text="Shape of the fruit or seed"
    )
    fruit_or_seed_persistence = models.BooleanField(
        null=True, default=False, 
        help_text="Do the fruits/seeds remain on the plant persistently?"
    )

    # Spacing details
    row_spacing_cm = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True, 
        help_text="Minimum spacing between rows (cm)"
    )
    spread_cm = models.DecimalField(
        max_digits=7, decimal_places=3, null=True, blank=True, 
        help_text="Average plant spread (cm)"
    )

    # Fields for plant care guide, which may be filled by API data or users:
    detailed_description = models.TextField(
        null=True, blank=True, 
        help_text="Full description and care guide for the plant"
    )
    care_instructions = models.TextField(
        null=True, blank=True, 
        help_text="Care instructions (watering, fertilization, pruning, etc.)"
    )
    watering_interval = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Recommended days between watering"
    )
    sunlight_requirements = models.CharField(
        max_length=100, null=True, blank=True, 
        help_text="E.g., 'Full sun', 'Partial shade'"
    )
    soil_type = models.CharField(
        max_length=100, null=True, blank=True, 
        help_text="Preferred soil type (e.g., well-draining loam)"
    )
    # Temperature tolerance (store in Celsius)
    min_temperature = models.IntegerField(
        null=True, blank=True, 
        help_text="Minimum tolerable temperature (°C)"
    )
    max_temperature = models.IntegerField(
        null=True, blank=True, 
        help_text="Maximum tolerable temperature (°C)"
    )
    nutrient_requirements = models.TextField(
        null=True, blank=True, 
        help_text="Notes on fertilizer or nutrient needs"
    )
    maintenance_notes = models.TextField(
        null=True, blank=True, 
        help_text="Additional maintenance or care notes"
    )
    
    # From the Trefle's 'growth' and 'specifications' sections:
    days_to_harvest = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, 
        help_text="Average number of days from planting to harvest"
    )
    sowing = models.TextField(
        null=True, blank=True, 
        help_text="Instructions on how to sow the plant"
    )
    ph_minimum = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, 
        help_text="Minimum acceptable soil pH"
    )
    ph_maximum = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, 
        help_text="Maximum acceptable soil pH"
    )
    light = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Required amount of light (scale 0-10)"
    )
    atmospheric_humidity = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Required relative atmospheric humidity (scale 0-10)"
    )
    minimum_precipitation = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Minimum annual precipitation in mm"
    )
    maximum_precipitation = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Maximum annual precipitation in mm"
    )
    minimum_root_depth = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Minimum root depth required (cm)"
    )
    # Storing months as JSON arrays (list of strings like "jan", "feb", etc.)
    growth_months = models.JSONField(
        null=True, blank=True, 
        help_text="Active growth months (list of month abbreviations)"
    )
    bloom_months = models.JSONField(
        null=True, blank=True, 
        help_text="Months in which the plant typically blooms"
    )
    fruit_months = models.JSONField(
        null=True, blank=True, 
        help_text="Months when the plant produces fruits"
    )
    growth_rate = models.CharField(
        max_length=50, null=True, blank=True, 
        help_text="Description of the plant's growth rate (e.g., 'Rapid')"
    )
    average_height = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Average plant height (cm)"
    )
    maximum_height = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Maximum plant height (cm)"
    )
    toxicity = models.CharField(
        max_length=50, null=True, blank=True, 
        help_text="Level of toxicity (e.g., 'none', 'low', etc.)"
    )

    # Fields for user-created plants
    is_user_created = models.BooleanField(
        default=False, 
        help_text="Indicates if this record was created by a user"
    )
    is_verified = models.BooleanField(
        default=False, 
        help_text="For user-submitted records, whether it has been verified by an admin"
    )
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="User who created this plant record"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.scientific_name} ({self.slug})"



    # class Meta:
    #     constraints = [
    #         CheckConstraint(
    #             check = Q(days_to_harvest__gte=0) or Q(days_to_harvest__isnull=True), 
    #             name = 'check_days_pos',
    #         ),

    #         CheckConstraint(
    #             check = (Q(ph_max__gte=0) and Q(ph_max__lte=14)) or Q(ph_max__isnull=True), 
    #             name = 'check_ph_max',
    #         ),

    #         CheckConstraint(
    #             check = (Q(ph_max__isnull=False) and Q(ph_min__gte=0) and Q(ph_min__lte=14) and Q(ph_min__lte=F('ph_max'))) or
    #             (Q(ph_max__isnull=True) and Q(ph_min__gte=0) and Q(ph_min__lte=14)) or
    #             Q(ph_min__isnull=True),
    #             name = 'check_ph_min',
    #         ),
    #         # Note: I think this accounts for if ph_max is null but ph_min is not...
    #         # To be honest, I don't understand clean methods yet, so I'm not sure if this
    #         # is the preferred route to do this.

    #         CheckConstraint(
    #             check = Q(row_spacing_cm__gte=0) or Q(row_spacing_cm__isnull=True), 
    #             name = 'check_row_pos',
    #         ),

    #         CheckConstraint(
    #             check = Q(spread_cm__gte=0) or Q(spread_cm__isnull=True), 
    #             name = 'check_spread_pos',
    #         ),

    #         CheckConstraint(
    #             check = Q(min_precip_mm__gte=0) or Q(min_precip_mm__isnull=True), 
    #             name = 'check_min_precip_pos',
    #         ),

    #         CheckConstraint(
    #             check = (Q(min_precip_mm__isnull=False) and Q(max_precip_mm__gte=0) and Q(max_precip_mm__gte=F('min_precip_mm'))) or
    #             (Q(min_precip_mm__isnull=True) and Q(max_precip_mm__gte=0)) or
    #             Q(max_precip_mm__isnull=True),
    #             name = 'check_max_precip_pos',
    #         ),
    #         # Note: I think this accounts for if min_precip is null but max_precip is not?

    #         CheckConstraint(
    #             check = Q(min_root_depth_cm__gte=0) or Q(min_root_depth_cm__isnull=True), 
    #             name = 'check_root_depth_pos',
    #         )
    #     ]
