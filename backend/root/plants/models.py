# backend/root/plants/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from model_utils import FieldTracker

User = get_user_model()

class Plant(models.Model):    
    # For permission management
    ADMIN_ONLY_FIELDS = [
        'api_id', 'slug', 'scientific_name', 'status', 'rank', 
        'family_common_name', 'family', 'genus_id', 'genus', 'synonyms',
        'vegetable', 'duration', 'edible', 'edible_part',
        'flower_color', 'flower_conspicuous', 'foliage_texture', 
        'foliage_color', 'foliage_retention', 'fruit_or_seed_conspicuous',
        'fruit_or_seed_color', 'fruit_or_seed_shape', 'fruit_or_seed_persistence',
        'row_spacing_cm', 'spread_cm', 'days_to_harvest', 'sowing',
        'ph_minimum', 'ph_maximum', 'light', 'atmospheric_humidity',
        'minimum_precipitation', 'maximum_precipitation', 'minimum_root_depth',
        'growth_months', 'bloom_months', 'fruit_months', 'growth_rate',
        'average_height', 'maximum_height', 'toxicity'
    ]

    # Fields that can be edited by users
    USER_EDITABLE_FIELDS = [
        'common_name', 'image_url', 'water_interval', 'fertilizing_interval', 'pruning_interval', 'sunlight_requirements',
        'soil_type', 'min_temperature', 'max_temperature', 
        'detailed_description', 'care_instructions', 
        'nutrient_requirements', 'maintenance_notes'
    ]
    
    # Required fields for user-created plants
    USER_REQUIRED_FIELDS = ['common_name', 'water_interval']
    
    # Methods for field access control
    def can_user_edit_field(self, user, field_name):
        """Check if a user can edit a specific field on this plant."""
        # Admins can edit anything
        if user.is_staff or user.role == 'Admin':
            return True
            
        # Users can only edit user-editable fields
        return field_name in self.USER_EDITABLE_FIELDS
    
    def clean(self):
        """Validate model data before saving."""
        super().clean()
        
        # For user-created plants, ensure required fields are present
        if self.is_user_created:
            for field_name in self.USER_REQUIRED_FIELDS:
                if getattr(self, field_name, None) in [None, '']:
                    raise ValidationError({
                        field_name: f"{field_name} is required for user-created plants"
                    })
        
    @classmethod
    def create_user_plant(cls, user, **kwargs):
        """Factory method to create a plant by a regular user."""
        # Ensure only allowed fields are set
        allowed_fields = cls.USER_EDITABLE_FIELDS + ['is_user_created', 'created_by']
        plant_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Set required metadata
        plant_data['is_user_created'] = True
        plant_data['created_by'] = user
        plant_data['is_verified'] = False
        
        # If slug not provided, generate one
        if 'slug' not in plant_data:
            from django.utils.text import slugify
            base_slug = slugify(plant_data.get('common_name', 'user-plant'))
            # Ensure unique slug
            slug = base_slug
            counter = 1
            while cls.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            plant_data['slug'] = slug
        
        # Create minimal scientific name if missing
        if 'scientific_name' not in plant_data:
            plant_data['scientific_name'] = f"User Plant: {plant_data.get('common_name', 'Unnamed')}"
            
        plant_data['rank'] = 'species'  # Default taxonomic rank
        plant_data['family'] = 'User Plants'  # Generic family for user plants
        
        # Extract genus from scientific name or use default
        if 'scientific_name' in plant_data and ' ' in plant_data['scientific_name']:
            # Use first word of scientific name as genus
            plant_data['genus'] = plant_data['scientific_name'].split()[0]
        else:
            plant_data['genus'] = 'UserPlantus'  # Default genus
            
        try:
            # Try to find if we have any existing user-created genus with this name
            from django.db import connection
            with connection.cursor() as cursor:
                # Find the max genus_id in use by our system to avoid conflicts
                cursor.execute("SELECT MAX(genus_id) FROM plants_plant")
                max_id = cursor.fetchone()[0] or 0
                
            # Use a high ID value beyond what the external taxonomy system would use
            plant_data['genus_id'] = max(10000000, max_id + 1000)
            
        except Exception:
            # If any database error occurs, fall back to a safer high value
            # Use hash of genus name to generate a consistent ID for the same genus
            import hashlib
            genus_hash = int(hashlib.md5(plant_data['genus'].encode('utf-8')).hexdigest(), 16)
            plant_data['genus_id'] = 20000000 + (genus_hash % 1000000)
            
        plant = cls(**plant_data)
        plant.full_clean()
        plant.save()
        return plant
        
    def save(self, *args, direct_save=False, **kwargs):
        """Save the plant, with optional validation bypass"""
        # Only run full validation if not saving directly
        if not direct_save:
            self.full_clean()
        
        # Get the current user from the context if available
        user = kwargs.pop('user', None)
        direct_save = kwargs.pop('direct_save', False)
        
        # If no user is provided or direct_save is True, just save normally 
        # (for admin operations, migrations, etc.)
        if not user or direct_save:
            return super().save(*args, **kwargs)
        
        # Use original instance if this is an existing record
        if self.pk:
            # Get the original plant from the database
            original = Plant.objects.get(pk=self.pk)
            
            # Check if this is a Trefle plant (has api_id) and not created by the user
            is_trefle_plant = self.api_id is not None and not self.is_user_created
            
            # Check if current user is the creator of a user plant
            is_creator = self.created_by == user
            
            # For Trefle plants, create change requests instead of direct saves
            if is_trefle_plant and not user.is_staff and user.role != 'Admin' and user.role != 'Moderator':
                # Find which fields have been changed
                for field_name in self.USER_EDITABLE_FIELDS:
                    old_value = getattr(original, field_name)
                    new_value = getattr(self, field_name)
                    
                    # If the field has changed, create a change request
                    if old_value != new_value:
                        PlantChangeRequest.objects.create(
                            plant=original,
                            user=user,
                            field_name=field_name,
                            old_value=old_value,
                            new_value=new_value
                        )
                
                # Return the original plant (changes are not applied directly)
                return original
            
            # For user plants, only the creator can edit
            elif not is_trefle_plant and not is_creator and not user.is_staff and user.role != 'Admin':
                raise PermissionDenied("You can only edit plants you've created")
        
        # Otherwise, proceed with normal save
        return super().save(*args, **kwargs)
        
    # Explicitly define the primary key field (Django would create this anyway)
    id = models.AutoField(primary_key=True)

    tracker = FieldTracker(fields=['is_verified']) # for signals

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

    # Fields for plant care guide, which will be filled by API data cleaning or users:
    detailed_description = models.TextField(
        null=True, blank=True, 
        help_text="Full description and care guide for the plant"
    )
    care_instructions = models.TextField(
        null=True, blank=True, 
        help_text="Care instructions (watering, fertilization, pruning, etc.)"
    )
    water_interval = models.PositiveIntegerField(
        null=False, blank=False, default=7,
        help_text="Recommended days between watering"
    )
    fertilizing_interval = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Recommended days between fertilizing"
    )
    pruning_interval = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Recommended days between pruning"
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
        max_digits=6, decimal_places=2, null=True, blank=True, 
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
    class Meta:
        indexes = [
            models.Index(fields=['common_name'], name='idx_plant_common_name'),
            models.Index(fields=['created_by'], name='idx_plant_created_by'),
        ]
        
        constraints = [
            models.CheckConstraint(
                check=models.Q(water_interval__gt=0),
                name='check_water_interval_positive'
            ),
            
            models.CheckConstraint(
                check=models.Q(days_to_harvest__gte=0) | models.Q(days_to_harvest__isnull=True), 
                name='check_days_pos',
            ),

            models.CheckConstraint(
                check=(models.Q(ph_maximum__gte=0) & models.Q(ph_maximum__lte=14)) | models.Q(ph_maximum__isnull=True), 
                name='check_ph_max',
            ),

            models.CheckConstraint(
                check=(models.Q(ph_maximum__isnull=False) & models.Q(ph_minimum__gte=0) & 
                    models.Q(ph_minimum__lte=14) & models.Q(ph_minimum__lte=models.F('ph_maximum'))) |
                    (models.Q(ph_maximum__isnull=True) & models.Q(ph_minimum__gte=0) & 
                    models.Q(ph_minimum__lte=14)) |
                    models.Q(ph_minimum__isnull=True),
                name='check_ph_min',
            ),

            models.CheckConstraint(
                check=models.Q(row_spacing_cm__gte=0) | models.Q(row_spacing_cm__isnull=True), 
                name='check_row_pos',
            ),

            models.CheckConstraint(
                check=models.Q(spread_cm__gte=0) | models.Q(spread_cm__isnull=True), 
                name='check_spread_pos',
            ),

            models.CheckConstraint(
                check=models.Q(minimum_precipitation__gte=0) | models.Q(minimum_precipitation__isnull=True), 
                name='check_min_precip_pos',
            ),

            models.CheckConstraint(
                check=(models.Q(minimum_precipitation__isnull=False) & 
                    models.Q(maximum_precipitation__gte=0) & 
                    models.Q(maximum_precipitation__gte=models.F('minimum_precipitation'))) |
                    (models.Q(minimum_precipitation__isnull=True) & 
                    models.Q(maximum_precipitation__gte=0)) |
                    models.Q(maximum_precipitation__isnull=True),
                name='check_max_precip_pos',
            ),

            models.CheckConstraint(
                check=models.Q(minimum_root_depth__gte=0) | models.Q(minimum_root_depth__isnull=True), 
                name='check_root_depth_pos',
            ),
            
            # Temperature check - make sure min_temperature is less than max_temperature if both exist
            models.CheckConstraint(
                check=(models.Q(min_temperature__isnull=True) | 
                    models.Q(max_temperature__isnull=True) | 
                    models.Q(min_temperature__lte=models.F('max_temperature'))),
                name='check_temperature_range',
            )
        ]

class PlantChangeRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='change_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(null=True, blank=True, help_text="User's reason for the change")
    reviewer = models.ForeignKey(
        User, null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='reviewed_changes'
    )
    review_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def approve(self, reviewer):
        """Approve the change and apply it to the plant"""
        self.status = 'APPROVED'
        self.reviewer = reviewer
        
        # Apply the change to the plant
        setattr(self.plant, self.field_name, self.new_value)
        
        # Save both models
        self.plant.save()
        self.save()
        
    def reject(self, reviewer, notes=None):
        """Reject the change request"""
        self.status = 'REJECTED'
        self.reviewer = reviewer
        if notes:
            self.review_notes = notes
        self.save()