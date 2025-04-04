# backend/root/plants/management/commands/import_full_trefle_data.py

import os
import time
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from plants.models import Plant
from services.trefle_service import list_plants, retrieve_plants
from services.plant_mapper import map_api_to_plant

logger = logging.getLogger(__name__)

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
            '--delay',
            type=float,
            default=0.6,
            help='Base delay in seconds between API calls (default: 0.6 seconds)'
        )

    def handle(self, *args, **options):
        max_pages = options.get('max_pages')
        delay = options['delay']
        page = 1
        total_imported = 0

        # Helper function for exponential backoff
        def get_with_backoff(func, *args, **kwargs):
            max_retries = 5
            base_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if the error message contains "429" (Too Many Requests)
                    if "429" in str(e) and attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        self.stdout.write(f"Rate limited. Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                    else:
                        raise

        self.stdout.write("Starting full Trefle data import process...")

        while True:
            try:
                list_response = list_plants(page=page)
            except Exception as e:
                self.stderr.write(f"Error fetching list page {page}: {e}")
                logger.exception("Error fetching list page %s", page)
                break

            plant_list = list_response.get('data', [])
            if not plant_list:
                self.stdout.write("No more plant records found on this page. Ending import.")
                break

            for basic_record in plant_list:
                plant_id = basic_record.get('slug') or basic_record.get('id')
                if not plant_id:
                    self.stderr.write("Skipping a record due to missing identifier.")
                    continue

                try:
                    # Use our backoff helper to wrap the retrieve call
                    full_response = get_with_backoff(retrieve_plants, plant_id)
                except Exception as e:
                    self.stderr.write(f"Error retrieving full data for plant {plant_id}: {e}")
                    logger.exception("Error retrieving full data for plant %s", plant_id)
                    continue

                full_data = full_response.get('data')
                if not full_data:
                    self.stderr.write(f"No full data found for plant {plant_id}.")
                    continue

                try:
                    mapped_data = map_api_to_plant(full_data)
                except Exception as e:
                    logger.error("Mapping error for plant %s: %s", plant_id, e)
                    continue

                unique_filter = {}
                if mapped_data.get("api_id"):
                    unique_filter["api_id"] = mapped_data["api_id"]
                else:
                    unique_filter["slug"] = mapped_data["slug"]

                try:
                    with transaction.atomic():
                        obj, created = Plant.objects.update_or_create(
                            **unique_filter,
                            defaults=mapped_data
                        )
                        total_imported += 1
                        self.stdout.write(f"Imported {mapped_data.get('slug')} (Total: {total_imported})")
                except Exception as e:
                    logger.error("Error saving plant %s: %s", mapped_data.get("slug"), e)
                    continue

                # Delay between each retrieve call (this delay is separate from backoff delays)
                time.sleep(delay)

            links = list_response.get('links', {})
            if not links.get('next'):
                self.stdout.write("No next page available in list endpoint. Import complete.")
                break

            page += 1
            if max_pages is not None and page > max_pages:
                self.stdout.write("Reached max_pages limit. Stopping import.")
                break

        self.stdout.write(self.style.SUCCESS(f"Full import complete. Total plants imported/updated: {total_imported}"))
