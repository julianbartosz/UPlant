# backend/root/plants/management/commands/fetch_trefle_raw.py

import os
import json
import time
import logging
from django.core.management.base import BaseCommand
from services.trefle_service import list_plants

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Fetch raw Trefle API plant data and store each page's response in a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            '--output_dir',
            type=str,
            default='trefle_raw_data',
            help='Directory to store raw API responses (default: trefle_raw_data)'
        )
        parser.add_argument(
            '--max_pages',
            type=int,
            default=None,
            help='Maximum number of pages to fetch (for testing purposes)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.6,
            help='Delay in seconds between API requests (default: 0.6 seconds)'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        max_pages = options.get('max_pages')
        delay = options['delay']

        # Create the output directory if it doesn't exist.
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(f"Created output directory: {output_dir}")

        page = 1
        total_plants = 0

        self.stdout.write("Starting raw Trefle API data fetch...")

        while True:
            if max_pages is not None and page > max_pages:
                self.stdout.write("Reached max_pages limit. Stopping.")
                break

            self.stdout.write(f"Fetching page {page}...")
            try:
                # Call the service function with the page parameter.
                response = list_plants(page=page)
            except Exception as e:
                self.stderr.write(f"Error fetching page {page}: {e}")
                logger.exception("Error fetching page %s", page)
                break

            # Save the raw JSON output for this page.
            output_path = os.path.join(output_dir, f"page_{page:05d}.json")
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)
                self.stdout.write(f"Saved page {page} data to {output_path}")
            except Exception as e:
                self.stderr.write(f"Error writing page {page} data: {e}")
                logger.exception("Error writing page %s data", page)
                break

            # Count the number of plants in this page.
            page_data = response.get('data', [])
            total_plants += len(page_data)

            # Check if there is a next page using the links section.
            links = response.get('links', {})
            if not links.get('next'):
                self.stdout.write("No next page found. Completed fetching all data.")
                break

            page += 1
            time.sleep(delay)  # Respect the API rate limit

        self.stdout.write(f"Fetched data for {page} pages with a total of {total_plants} plants.")
        self.stdout.write("Raw data fetch complete.")
