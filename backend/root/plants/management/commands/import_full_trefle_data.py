# backend/root/plants/management/commands/import_full_trefle_data.py

import os
import timey
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from plants.models import Plant
from services.trefle_service import list_plants, retrieve_plants
from services.plant_mapper import map_api_to_plant

logger = logging.getLogger(__name__)

def get_with_backoff(func, *args, max_retries=3, initial_delay=1, **kwargs):
    """Helper function to retry API calls with exponential backoff"""
    attempt = 0
    while attempt < max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                raise
            sleep_time = initial_delay * (2 ** (attempt - 1))
            logger.warning(f"API call failed, retrying in {sleep_time}s: {e}")
            time.sleep(sleep_time)

class Command(BaseCommand):
    help = "Import full Trefle plant data into the database using the retrieve endpoint."

    def add_arguments(self, parser):
        parser.add_argument(
            '--max_pages',
            type=int,
            default=None,
            help='Maximum number of pages from the list endpoint to process (for testing)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of plants per page'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug output'
        )

    def handle(self, *args, **options):
        max_pages = options.get('max_pages')
        limit = options.get('limit')
        debug = options.get('debug', False)
        
        page_number = 1
        total_imported = 0
        
        self.stdout.write(f"Starting plant import (max_pages={max_pages}, limit={limit})")
        
        while True:
            if max_pages and page_number > max_pages:
                self.stdout.write(f"Reached page limit ({max_pages}). Stopping import.")
                break
                
            self.stdout.write(f"Fetching page {page_number} of plants...")
            
            try:
                list_response = get_with_backoff(
                    list_plants, 
                    filters={"limit": limit},
                    page=page_number
                )
                
                plant_list = list_response.get('data', [])
                
                if not plant_list:
                    self.stdout.write("No more plant records found on this page. Ending import.")
                    break
                
                # Process each plant in the current page
                for basic_record in plant_list:
                    plant_id = basic_record.get('slug') or basic_record.get('id')
                    if not plant_id:
                        self.stderr.write("Skipping a record due to missing identifier.")
                        continue
                    
                    try:
                        # Get detailed plant information using retrieve_plants
                        self.stdout.write(f"Fetching detailed data for plant {plant_id}...")
                        full_response = get_with_backoff(retrieve_plants, plant_id)
                        
                        if debug:
                            self.stdout.write(f"Retrieved plant data: {full_response}")
                        
                        # Check if we got valid data back
                        full_data = full_response.get('data')
                        if not full_data:
                            self.stderr.write(f"No full data found for plant {plant_id}.")
                            continue
                        
                        # Create or update plant record in database
                        try:
                            with transaction.atomic():
                                # Convert API data to our model format
                                plant_fields = map_api_to_plant(full_data)
                                
                                # Debug output
                                if debug:
                                    self.stdout.write(f"Mapped fields: {plant_fields}")
                                
                                # Check for required fields
                                if not plant_fields.get('scientific_name'):
                                    self.stderr.write(f"Missing scientific name for plant {plant_id}. Skipping.")
                                    continue
                                
                                # Use update_or_create to either update existing record or create new one
                                plant, created = Plant.objects.update_or_create(
                                    api_id=str(full_data.get('id')),
                                    defaults=plant_fields
                                )
                                
                                action = "Created" if created else "Updated"
                                self.stdout.write(f"{action} plant: {plant.scientific_name}")
                                total_imported += 1
                                
                        except Exception as e:
                            self.stderr.write(f"Error saving plant {plant_id}: {e}")
                            logger.exception(f"Failed to save plant record for {plant_id}")
                    
                    except Exception as e:
                        self.stderr.write(f"Error retrieving full data for plant {plant_id}: {e}")
                        logger.exception(f"Error retrieving full data for plant {plant_id}")
                        continue
                
                # Move to next page
                page_number += 1
                
                # Add a small delay to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                self.stderr.write(f"Error fetching plant list page {page_number}: {e}")
                logger.exception(f"Error fetching plant list page {page_number}")
                break
        
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {total_imported} plants"))