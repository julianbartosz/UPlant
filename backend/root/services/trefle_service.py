# backend/root/services/trefle_service.py

import os
import requests
import logging
from django.conf import settings
from django.core.cache import cache
from requests.exceptions import RequestException, Timeout

# Configure logging
logger = logging.getLogger(__name__)

# Constants
TREFLE_BASE_URL = "https://trefle.io/api/v1"
TREFLE_API_KEY = settings.TREFLE_API_KEY if hasattr(settings, 'TREFLE_API_KEY') else os.getenv('TREFLE_API')
REQUEST_TIMEOUT = 10  # seconds
CACHE_TIMEOUT = 300  # 5 minutes in seconds

def _get_headers():
    """Return the default headers for Trefle API requests."""
    return {
        "Authorization": f"Bearer {TREFLE_API_KEY}"
    }

def _make_request(url, params=None):
    """
    Make a request to the Trefle API with error handling and caching.
    
    Args:
        url: The API endpoint URL
        params: Optional query parameters
        
    Returns:
        dict: API response data or error message
    """
    # Create cache key from URL and params
    cache_key = f"trefle_{url}_{str(params)}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.debug(f"Returning cached data for {url}")
        return cached_data
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=_get_headers(),
            timeout=REQUEST_TIMEOUT
        )
        
        # Raise exception for 4XX/5XX status codes
        response.raise_for_status()
        
        data = response.json()
        
        # Cache successful responses
        cache.set(cache_key, data, CACHE_TIMEOUT)
        
        return data
        
    except Timeout:
        logger.error(f"Timeout error accessing Trefle API: {url}")
        return {"error": "The request to the plant database timed out. Please try again later."}
        
    except RequestException as e:
        logger.error(f"Error accessing Trefle API: {str(e)}")
        
        # Handle common status codes with user-friendly messages
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            if status_code == 401:
                return {"error": "Authentication error with the plant database. Please contact support."}
            elif status_code == 404:
                return {"error": "The requested plant information could not be found."}
            elif status_code == 429:
                return {"error": "Too many requests to the plant database. Please try again later."}
            elif status_code >= 500:
                return {"error": "The plant database service is currently unavailable. Please try again later."}
        
        return {"error": "An error occurred while fetching plant data. Please try again later."}
    
    except Exception as e:
        logger.error(f"Unexpected error in Trefle API request: {str(e)}")
        return {"error": "An unexpected error occurred. Please try again later."}

def list_species(filters=None, page=1):
    """
    List plant species with optional filters and pagination.
    
    Args:
        filters (dict): Optional filter parameters
        page (int): Page number for paginated results
        
    Returns:
        dict: List of plant species or error message
    """
    url = f"{TREFLE_BASE_URL}/species"
    
    # Initialize params with page number
    params = {"page": page}
    
    # Add any filters to the params
    if filters and isinstance(filters, dict):
        params.update(filters)
    
    return _make_request(url, params)

def retrieve_species(species_id_or_slug):
    """
    Retrieve detailed information about a specific plant species.
    
    Args:
        species_id_or_slug: The ID or slug of the species to retrieve
        
    Returns:
        dict: Species data or error message
    """
    url = f"{TREFLE_BASE_URL}/species/{species_id_or_slug}"
    return _make_request(url)

def search_species(query, page=1, filters=None):
    """
    Search for plant species matching a query with optional filters.
    
    Args:
        query (str): Search term
        page (int): Page number for paginated results
        filters (dict): Optional filter parameters
        
    Returns:
        dict: Search results or error message
    """
    url = f"{TREFLE_BASE_URL}/species/search"
    
    # Initialize params with search query and page number
    params = {"q": query, "page": page}
    
    # Add any filters to the params
    if filters and isinstance(filters, dict):
        params.update(filters)
    
    return _make_request(url, params)

def get_plant_distributions(species_id_or_slug):
    """
    Get geographical distribution data for a plant species.
    
    Args:
        species_id_or_slug: The ID or slug of the species
        
    Returns:
        dict: Distribution data or error message
    """
    url = f"{TREFLE_BASE_URL}/species/{species_id_or_slug}/distributions"
    return _make_request(url)

def get_genus_data(genus_id_or_slug):
    """
    Get information about a specific plant genus.
    
    Args:
        genus_id_or_slug: The ID or slug of the genus
        
    Returns:
        dict: Genus data or error message
    """
    url = f"{TREFLE_BASE_URL}/genus/{genus_id_or_slug}"
    return _make_request(url)

def get_kingdom_data():
    """
    Get information about plant kingdoms.
    
    Returns:
        dict: Kingdom data or error message
    """
    url = f"{TREFLE_BASE_URL}/kingdoms"
    return _make_request(url)