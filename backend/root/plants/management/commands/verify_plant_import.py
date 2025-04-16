# backend/root/plants/management/commands/verify_plant_import.py

from django.core.management.base import BaseCommand
from plants.models import Plant
from django.db.models import Q

class Command(BaseCommand):
    help = "Verify plant import contains detailed data"

    def handle(self, *args, **options):
        total = Plant.objects.count()
        self.stdout.write(f"Total plants: {total}")
        
        if total == 0:
            self.stdout.write(self.style.ERROR("No plants found!"))
            return
        
        # List of fields that should only be present if retrieve_plants was used
        numeric_fields = [
            'min_temperature',
            'max_temperature',
            'atmospheric_humidity',
            'light',
        ]
        
        array_fields = [
            'bloom_months',
            'fruit_months',
            'growth_months',
        ]
        
        boolean_fields = [
            'vegetable',
        ]
        
        text_fields = [
            'edible_part',
            'toxicity',
        ]
        
        # Track statistics
        field_counts = {}
        
        # Check numeric fields for non-null values
        self.stdout.write("\nNumeric field statistics:")
        for field in numeric_fields:
            field_counts[field] = Plant.objects.filter(~Q(**{f"{field}__isnull": True})).count()
            percentage = field_counts[field] / total * 100 if total > 0 else 0
            self.stdout.write(f"  {field}: {field_counts[field]} plants ({percentage:.1f}%)")
        
        # Check array fields for non-empty lists
        self.stdout.write("\nArray field statistics:")
        for field in array_fields:
            # Handle JSON fields differently 
            try:
                field_counts[field] = Plant.objects.exclude(**{f"{field}": None}).exclude(**{f"{field}": []}).count()
            except:
                # Fallback if field format is unexpected
                field_counts[field] = 0
            
            percentage = field_counts[field] / total * 100 if total > 0 else 0
            self.stdout.write(f"  {field}: {field_counts[field]} plants ({percentage:.1f}%)")
        
        # Check boolean fields
        self.stdout.write("\nBoolean field statistics:")
        for field in boolean_fields:
            field_counts[field] = Plant.objects.filter(**{f"{field}": True}).count()
            percentage = field_counts[field] / total * 100 if total > 0 else 0
            self.stdout.write(f"  {field}: {field_counts[field]} plants ({percentage:.1f}%)")
        
        # Check text fields
        self.stdout.write("\nText field statistics:")
        for field in text_fields:
            field_counts[field] = Plant.objects.exclude(**{f"{field}": None}).exclude(**{f"{field}": ""}).count()
            percentage = field_counts[field] / total * 100 if total > 0 else 0
            self.stdout.write(f"  {field}: {field_counts[field]} plants ({percentage:.1f}%)")
        
        # Overall assessment
        has_detailed_data = any(count > 0 for count in field_counts.values())
        
        if has_detailed_data:
            self.stdout.write(self.style.SUCCESS("\n✅ Import appears successful with detailed data!"))
            
            # Find and display a sample plant with detailed data
            for field, count in field_counts.items():
                if count > 0:
                    # Get a sample plant with this field populated
                    if field in numeric_fields:
                        sample = Plant.objects.filter(~Q(**{f"{field}__isnull": True})).first()
                    elif field in boolean_fields:
                        sample = Plant.objects.filter(**{f"{field}": True}).first()
                    else:
                        sample = Plant.objects.exclude(**{f"{field}": None}).exclude(**{f"{field}": ""}).first()
                    
                    if sample:
                        self.stdout.write(f"\nSample plant with detailed data: {sample.common_name} ({sample.scientific_name})")
                        self.stdout.write(f"  {field}: {getattr(sample, field)}")
                    break
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Import may not have included detailed data!"))