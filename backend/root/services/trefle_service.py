# backend/root/services/trefle_service.py

import os
import requests
import logging
from django.conf import settings
from django.core.cache import cache
from requests.exceptions import RequestException, Timeout
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Constants
TREFLE_BASE_URL = "https://trefle.io/api/v1"
TREFLE_API_KEY = (
    settings.TREFLE_API_KEY if hasattr(settings, "TREFLE_API_KEY") else os.getenv("TREFLE_API")
)
REQUEST_TIMEOUT = 10  # seconds
CACHE_TIMEOUT = 300   # 5 minutes in seconds

# Persistent session for connection reuse
session = requests.Session()

# Custom exception for API errors
class TrefleAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

# Pydantic model for simplified plant data
class PlantModel(BaseModel):
    id: int
    common_name: Optional[str] = ""
    slug: str
    scientific_name: str
    status: Optional[str] = ""
    rank: Optional[str] = ""
    family_common_name: Optional[str] = ""
    family: Optional[str] = ""
    genus_id: Optional[int] = None
    genus: Optional[str] = ""
    image_url: Optional[str] = ""
    synonyms: List[str] = []
    links: Dict[str, Any] = {}

def _sorted_params_str(params: Dict) -> str:
    """Return a string of sorted query parameter items for cache key consistency."""
    return str(sorted(params.items()))

def _make_request_query_auth(url: str, params: Optional[Dict] = None) -> Dict:
    """
    Make a request to the Trefle API using query parameter authentication.
    Adds the API token as a query parameter, uses a persistent session,
    handles errors (raising TrefleAPIError), ensures JSON decoding, and caches the response.
    """
    if params is None:
        params = {}
    # Add token authentication via query parameter
    params["token"] = TREFLE_API_KEY

    # Build a consistent cache key from sorted parameters
    sorted_params = _sorted_params_str(params)
    cache_key = f"trefle_{url}_{sorted_params}"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Returning cached data for {url} with params {params}")
        return cached_data

    try:
        logger.debug(f"Making request to {url} with params {params}")
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"JSON decoding failed for {url}: {str(e)}")
            raise TrefleAPIError("Failed to decode JSON response", status_code=response.status_code)
        cache.set(cache_key, data, CACHE_TIMEOUT)
        return data
    except Timeout:
        logger.error(f"Timeout error accessing {url} with params {params}")
        raise TrefleAPIError("The request to the plant database timed out. Please try again later.")
    except RequestException as e:
        status_code = e.response.status_code if e.response else None
        logger.error(f"RequestException for {url} with params {params}: {str(e)}")
        if status_code == 401:
            raise TrefleAPIError("Authentication error with the plant database. Please contact support.", status_code=401)
        elif status_code == 404:
            raise TrefleAPIError("The requested plant information could not be found.", status_code=404)
        elif status_code == 429:
            raise TrefleAPIError("Too many requests to the plant database. Please try again later.", status_code=429)
        elif status_code and status_code >= 500:
            raise TrefleAPIError("The plant database service is currently unavailable. Please try again later.", status_code=status_code)
        raise TrefleAPIError("An error occurred while fetching plant data. Please try again later.", status_code=status_code)
    except Exception as e:
        logger.error(f"Unexpected error for {url} with params {params}: {str(e)}")
        raise TrefleAPIError("An unexpected error occurred. Please try again later.")

def _process_single_plant(plant: Dict) -> Dict:
    """
    Process and simplify a single plant object.
    Validates and transforms the raw plant data using the PlantModel.
    """
    # Ensure required keys have default values
    plant.setdefault("id", None)
    plant.setdefault("slug", None)
    plant.setdefault("scientific_name", None)
    plant.setdefault("common_name", "")
    plant.setdefault("status", "")
    plant.setdefault("rank", "")
    plant.setdefault("family_common_name", "")
    plant.setdefault("family", "")
    plant.setdefault("genus_id", None)
    plant.setdefault("genus", "")
    plant.setdefault("image_url", "")
    if not isinstance(plant.get("synonyms"), list):
        plant["synonyms"] = []
    if not isinstance(plant.get("links"), dict):
        plant["links"] = {}

    try:
        validated = PlantModel(**plant)
        return validated.dict()
    except ValidationError as e:
        logger.error(f"Validation error processing plant data: {e.json()}")
        raise TrefleAPIError("Received invalid plant data from API.")

def _process_plant_data(raw_data: Dict) -> Dict:
    """
    Process the raw API response data and return a simplified, validated structure.
    Handles both single plant and list of plants.
    """
    if "error" in raw_data:
        raise TrefleAPIError(raw_data.get("error"))
    data = raw_data.get("data")
    if data is None:
        logger.error("No 'data' key found in API response.")
        raise TrefleAPIError("Malformed response from plant API.")

    if isinstance(data, list):
        processed_list = [_process_single_plant(plant) for plant in data]
        return {
            "data": processed_list,
            "links": raw_data.get("links", {}),
            "meta": raw_data.get("meta", {})
        }
    elif isinstance(data, dict):
        processed_plant = _process_single_plant(data)
        return {"data": processed_plant}
    else:
        logger.error("Unexpected data format in API response.")
        raise TrefleAPIError("Unexpected data format received from plant API.")

def list_plants(filters: Optional[Dict] = None, page: int = 1,
                order: Optional[Dict] = None, range: Optional[Dict] = None) -> Dict:
    """
    List plants using the Trefle API with query parameter authentication.
    Supports additional query parameters for filtering, ordering, and range filtering.
    Processes the raw API response into a simplified, validated structure.
    
    Args:
        filters (dict): Filter parameters (e.g., {"common_name": "rose"}).
        page (int): Page number for pagination.
        order (dict): Sort orders (e.g., {"year": "asc", "common_name": "desc"}).
        range (dict): Range filters (e.g., {"year": "1800-1900"}).
        
    Returns:
        dict: Simplified API response containing plant data.
    """
    url = f"{TREFLE_BASE_URL}/plants"
    params = {"page": page}
    if filters and isinstance(filters, dict):
        params.update(filters)
    if order and isinstance(order, dict):
        order_str = ",".join([f"{k}:{v}" for k, v in order.items()])
        params["order"] = order_str
    if range and isinstance(range, dict):
        range_str = ",".join([f"{k}:{v}" for k, v in range.items()])
        params["range"] = range_str

    raw_response = _make_request_query_auth(url, params)
    return _process_plant_data(raw_response)

def retrieve_plants(species_id_or_slug: str) -> Dict:
    """
    Retrieve a single plant's details from the Trefle API using query parameter authentication.
    Processes the raw API response into a simplified, validated structure.
    
    Args:
        species_id_or_slug (str): The unique identifier or slug of the plant.
        
    Returns:
        dict: Simplified plant data.
    """
    url = f"{TREFLE_BASE_URL}/plants/{species_id_or_slug}"
    raw_response = _make_request_query_auth(url)
    return _process_plant_data(raw_response)
