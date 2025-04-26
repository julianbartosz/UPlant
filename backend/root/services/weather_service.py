# backend/root/services/weather_service.py

import requests
import logging
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# API Configuration
FORECAST_BASE_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ZIP_GEOCODING_URL = "https://nominatim.openstreetmap.org/search"  # OpenStreetMap for ZIP codes
DEFAULT_TIMEZONE = "auto"  # Use 'auto' to determine timezone from coordinates
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Cache configuration
CACHE_DURATION = 3600  # 1 hour in seconds
# Simple in-memory cache
_weather_cache = {}
_geocode_cache = {}

class WeatherServiceError(Exception):
    """Custom exception for weather service errors"""
    pass

def _make_api_request(url: str, params: Dict[str, Any]) -> Dict:
    """
    Make API request with retry logic
    
    Args:
        url: API endpoint URL
        params: Query parameters
        
    Returns:
        Dictionary with API response
        
    Raises:
        WeatherServiceError: If request fails after retries
    """
    # Add proper headers for OpenStreetMap Nominatim API
    headers = {}
    
    if "nominatim.openstreetmap.org" in url:
        headers = {
            'User-Agent': 'UPlant/1.0 (http://localhost:5173; uplant.notifications@gmail.com)',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'http://localhost:5173'
        }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"API request failed (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"API request failed after {MAX_RETRIES} attempts: {str(e)}")
                raise WeatherServiceError(f"Weather service unavailable: {str(e)}")
            
def get_coordinates_from_zip(zip_code: str, country: str = "us") -> Tuple[float, float]:
    """
    Convert ZIP code to coordinates (latitude, longitude)
    
    Args:
        zip_code: ZIP/Postal code
        country: Country code (default: us)
        
    Returns:
        Tuple of (latitude, longitude)
        
    Raises:
        WeatherServiceError: If ZIP code cannot be geocoded
    """
    cache_key = f"{zip_code}:{country}"
    
    # Check cache first
    if cache_key in _geocode_cache:
        timestamp, coords = _geocode_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            logger.debug(f"Using cached coordinates for {zip_code}")
            return coords
    
    # First try OpenStreetMap for ZIP code lookup
    params = {
        "postalcode": zip_code,
        "country": country,
        "format": "json",
        "limit": 1
    }
    
    try:
        response = _make_api_request(ZIP_GEOCODING_URL, params)
        
        if response and len(response) > 0:
            lat = float(response[0]["lat"])
            lon = float(response[0]["lon"])
            
            # Cache the result
            _geocode_cache[cache_key] = (time.time(), (lat, lon))
            return lat, lon
        
        # If we get an empty response, try Open-Meteo geocoding as fallback
        # using the ZIP code as a query (less accurate)
        logger.warning(f"ZIP code {zip_code} not found, trying as place name")
        return get_coordinates_from_place(zip_code)
        
    except Exception as e:
        logger.error(f"Error geocoding ZIP code {zip_code}: {str(e)}")
        raise WeatherServiceError(f"Could not find coordinates for ZIP code {zip_code}")

def get_coordinates_from_place(place_name: str) -> Tuple[float, float]:
    """
    Get coordinates from a place name using Open-Meteo's geocoding API
    
    Args:
        place_name: Name of city, town, or location
        
    Returns:
        Tuple of (latitude, longitude)
        
    Raises:
        WeatherServiceError: If place cannot be geocoded
    """
    cache_key = f"place:{place_name}"
    
    # Check cache first
    if cache_key in _geocode_cache:
        timestamp, coords = _geocode_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return coords
    
    params = {
        "name": place_name,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    try:
        response = _make_api_request(GEOCODING_BASE_URL, params)
        
        if response and "results" in response and len(response["results"]) > 0:
            result = response["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            
            # Cache the result
            _geocode_cache[cache_key] = (time.time(), (lat, lon))
            return lat, lon
        else:
            raise WeatherServiceError(f"Could not geocode place: {place_name}")
            
    except Exception as e:
        if not isinstance(e, WeatherServiceError):
            logger.error(f"Error geocoding place {place_name}: {str(e)}")
            raise WeatherServiceError(f"Could not find coordinates for {place_name}")
        raise

def get_current_weather(lat: float, lon: float, timezone: str = DEFAULT_TIMEZONE) -> Dict[str, Any]:
    """
    Get current weather for coordinates
    
    Args:
        lat: Latitude
        lon: Longitude
        timezone: Timezone (default: auto)
        
    Returns:
        Dictionary with current weather data
    """
    cache_key = f"current:{lat:.4f}:{lon:.4f}"
    
    # Check cache
    if cache_key in _weather_cache:
        timestamp, data = _weather_cache[cache_key]
        if time.time() - timestamp < 900:  # 15 min cache for current weather
            return data
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "current_weather": True,
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "snowfall", 
                    "cloud_cover", "wind_speed_10m", "wind_direction_10m"],
    }
    
    response = _make_api_request(FORECAST_BASE_URL, params)
    
    # Process the response into a more user-friendly format
    if "current" in response:
        result = {
            "temperature": {
                "value": response["current"]["temperature_2m"],
                "unit": response["current_units"]["temperature_2m"]
            },
            "humidity": {
                "value": response["current"]["relative_humidity_2m"],
                "unit": response["current_units"]["relative_humidity_2m"]
            },
            "wind_speed": {
                "value": response["current"]["wind_speed_10m"],
                "unit": response["current_units"]["wind_speed_10m"]
            },
            "wind_direction": response["current"]["wind_direction_10m"],
            "rain": {
                "value": response["current"]["rain"],
                "unit": response["current_units"]["rain"]
            },
            "cloud_cover": {
                "value": response["current"]["cloud_cover"],
                "unit": response["current_units"]["cloud_cover"]
            },
            "time": response["current"]["time"]
        }
    else:
        # Fallback to older API version format
        result = response.get("current_weather", {})
        
    # Cache the result
    _weather_cache[cache_key] = (time.time(), result)
    return result

def get_daily_forecast(
    lat: float, 
    lon: float, 
    days: int = 7, 
    timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
    """
    Get daily weather forecast
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of days to forecast
        timezone: Timezone (default: auto)
        
    Returns:
        Dictionary with daily forecast data
    """
    cache_key = f"daily:{lat:.4f}:{lon:.4f}:{days}"
    
    # Check cache
    if cache_key in _weather_cache:
        timestamp, data = _weather_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    
    # Garden-relevant variables
    daily_variables = [
        "temperature_2m_max", 
        "temperature_2m_min",
        "precipitation_sum",
        "rain_sum",
        "snowfall_sum",
        "precipitation_hours",
        "precipitation_probability_max",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "sunshine_duration", 
        "uv_index_max",
        "soil_temperature_0cm",
    ]
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "daily": ",".join(daily_variables),
        "forecast_days": days
    }
    
    response = _make_api_request(FORECAST_BASE_URL, params)
    
    # Process the response
    result = {
        "timezone": response.get("timezone", timezone),
        "daily": []
    }
    
    daily_data = response.get("daily", {})
    time_data = daily_data.get("time", [])
    
    for i in range(len(time_data)):
        day_data = {
            "date": time_data[i],
            "temperature": {
                "max": {
                    "value": daily_data["temperature_2m_max"][i],
                    "unit": response["daily_units"]["temperature_2m_max"]
                },
                "min": {
                    "value": daily_data["temperature_2m_min"][i],
                    "unit": response["daily_units"]["temperature_2m_min"]
                }
            },
            "precipitation": {
                "sum": {
                    "value": daily_data["precipitation_sum"][i],
                    "unit": response["daily_units"]["precipitation_sum"]
                },
                "rain": {
                    "value": daily_data["rain_sum"][i],
                    "unit": response["daily_units"]["rain_sum"]
                },
                "snowfall": {
                    "value": daily_data["snowfall_sum"][i],
                    "unit": response["daily_units"]["snowfall_sum"]
                },
                "hours": daily_data["precipitation_hours"][i],
                "probability": daily_data["precipitation_probability_max"][i]
            },
            "wind": {
                "speed": {
                    "value": daily_data["wind_speed_10m_max"][i],
                    "unit": response["daily_units"]["wind_speed_10m_max"]
                },
                "gusts": {
                    "value": daily_data["wind_gusts_10m_max"][i],
                    "unit": response["daily_units"]["wind_gusts_10m_max"]
                }
            },
            "sunshine_duration": {
                "value": daily_data.get("sunshine_duration", [0]*len(time_data))[i],
                "unit": response["daily_units"].get("sunshine_duration", "hours")
            },
            "uv_index": daily_data.get("uv_index_max", [0]*len(time_data))[i],
            "soil_temperature": {
                "value": daily_data.get("soil_temperature_0cm", [None]*len(time_data))[i],
                "unit": response["daily_units"].get("soil_temperature_0cm", "°C")
            }
        }
        result["daily"].append(day_data)
    
    # Cache the result
    _weather_cache[cache_key] = (time.time(), result)
    return result

def get_garden_weather_insights(zip_code: str) -> Dict[str, Any]:
    """
    Get garden-relevant weather insights based on a ZIP code
    
    Args:
        zip_code: ZIP/postal code
        
    Returns:
        Dictionary with garden weather insights
    """
    try:
        # Get coordinates from ZIP code
        lat, lon = get_coordinates_from_zip(zip_code)
        
        # Get current weather and forecast
        current = get_current_weather(lat, lon)
        forecast = get_daily_forecast(lat, lon, days=7)
        
        # Generate garden-specific insights
        insights = {
            "watering_needed": _calculate_watering_advice(current, forecast),
            "frost_warning": _check_for_frost(forecast),
            "extreme_heat_warning": _check_for_extreme_heat(forecast),
            "high_wind_warning": _check_for_high_winds(forecast),
            "current_weather": current,
            "forecast_summary": _generate_forecast_summary(forecast),
            "coordinates": {"latitude": lat, "longitude": lon}
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting garden weather insights for ZIP {zip_code}: {str(e)}")
        raise WeatherServiceError(f"Could not get weather insights: {str(e)}")

def _calculate_watering_advice(current: Dict, forecast: Dict) -> Dict:
    """Calculate if watering is needed based on current conditions and forecast"""
    recent_rain = current.get("rain", {}).get("value", 0) > 0
    
    # Check forecast for upcoming rain
    rain_coming = False
    rain_probability = 0
    for i, day in enumerate(forecast.get("daily", [])):
        if i > 2:  # Only check next 3 days
            break
        if day["precipitation"]["rain"]["value"] > 5:  # More than 5mm rain expected
            rain_coming = True
            rain_probability = max(rain_probability, day["precipitation"]["probability"])
    
    # Calculate soil moisture estimate (simplified)
    current_temp = current.get("temperature", {}).get("value", 20)
    humidity = current.get("humidity", {}).get("value", 50)
    
    # Simple heuristic: higher temp and lower humidity = drier soil
    dryness_factor = current_temp / 10 - humidity / 20
    
    result = {
        "should_water": not recent_rain and not rain_coming and dryness_factor > 0,
        "reason": "",
        "next_rain_forecast": None,
        "rain_probability": rain_probability
    }
    
    if recent_rain:
        result["reason"] = "Recent rainfall detected"
    elif rain_coming:
        result["reason"] = f"Rain forecasted in the next few days ({rain_probability}% probability)"
        # Find next rain day
        for day in forecast.get("daily", []):
            if day["precipitation"]["rain"]["value"] > 1:
                result["next_rain_forecast"] = day["date"]
                break
    else:
        if dryness_factor > 4:
            result["reason"] = "Very dry conditions detected"
        elif dryness_factor > 0:
            result["reason"] = "Moderate watering recommended"
        else:
            result["reason"] = "Soil moisture likely adequate"
            result["should_water"] = False
            
    return result

def _check_for_frost(forecast: Dict) -> Dict:
    """Check for frost conditions in the forecast"""
    result = {
        "frost_risk": False,
        "frost_days": [],
        "min_temperature": None
    }
    
    for day in forecast.get("daily", []):
        if day["temperature"]["min"]["value"] <= 0:
            result["frost_risk"] = True
            result["frost_days"].append({
                "date": day["date"],
                "temperature": day["temperature"]["min"]["value"]
            })
            
            if result["min_temperature"] is None or day["temperature"]["min"]["value"] < result["min_temperature"]:
                result["min_temperature"] = day["temperature"]["min"]["value"]
                
    return result

def _check_for_extreme_heat(forecast: Dict) -> Dict:
    """Check for extreme heat conditions in the forecast"""
    result = {
        "extreme_heat": False,
        "hot_days": [],
        "max_temperature": None
    }
    
    for day in forecast.get("daily", []):
        if day["temperature"]["max"]["value"] >= 32:  # >32°C / 90°F is considered very hot
            result["extreme_heat"] = True
            result["hot_days"].append({
                "date": day["date"],
                "temperature": day["temperature"]["max"]["value"]
            })
            
            if result["max_temperature"] is None or day["temperature"]["max"]["value"] > result["max_temperature"]:
                result["max_temperature"] = day["temperature"]["max"]["value"]
                
    return result

def _check_for_high_winds(forecast: Dict) -> Dict:
    """Check for high wind conditions in the forecast"""
    result = {
        "high_winds": False,
        "windy_days": [],
        "max_wind_speed": None
    }
    
    for day in forecast.get("daily", []):
        # Wind speed > 20 km/h or 12 mph can affect plants
        if day["wind"]["speed"]["value"] > 20:
            result["high_winds"] = True
            result["windy_days"].append({
                "date": day["date"],
                "wind_speed": day["wind"]["speed"]["value"],
                "wind_gusts": day["wind"]["gusts"]["value"]
            })
            
            if result["max_wind_speed"] is None or day["wind"]["speed"]["value"] > result["max_wind_speed"]:
                result["max_wind_speed"] = day["wind"]["speed"]["value"]
                
    return result

def _generate_forecast_summary(forecast: Dict) -> Dict:
    """Generate a summary of the weather forecast"""
    total_rain = sum(day["precipitation"]["rain"]["value"] for day in forecast.get("daily", []))
    avg_max_temp = sum(day["temperature"]["max"]["value"] for day in forecast.get("daily", [])) / len(forecast.get("daily", []))
    avg_min_temp = sum(day["temperature"]["min"]["value"] for day in forecast.get("daily", [])) / len(forecast.get("daily", []))
    
    return {
        "period": f"{forecast.get('daily', [])[0]['date']} to {forecast.get('daily', [])[-1]['date']}",
        "total_rainfall": round(total_rain, 1),
        "average_high": round(avg_max_temp, 1),
        "average_low": round(avg_min_temp, 1),
        "rainiest_day": max(forecast.get("daily", []), key=lambda x: x["precipitation"]["rain"]["value"])["date"] if forecast.get("daily") else None,
        "hottest_day": max(forecast.get("daily", []), key=lambda x: x["temperature"]["max"]["value"])["date"] if forecast.get("daily") else None,
        "coldest_day": min(forecast.get("daily", []), key=lambda x: x["temperature"]["min"]["value"])["date"] if forecast.get("daily") else None
    }

def get_weather_by_zip(zip_code: str) -> Dict[str, Any]:
    """Get weather by ZIP code"""
    lat, lon = get_coordinates_from_zip(zip_code)
    
    # Fixed daily parameters (removed soil_temperature_0cm)
    daily_params = [
        "temperature_2m_max", "temperature_2m_min",
        "precipitation_sum", "rain_sum", "snowfall_sum",
        "precipitation_hours", "precipitation_probability_max",
        "wind_speed_10m_max", "wind_gusts_10m_max",
        "sunshine_duration", "uv_index_max"
    ]
    
    # Build the API URL with correct parameters
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "daily": ",".join(daily_params),
        "forecast_days": 7
    }
    
    try:
        # Make the API request
        response = _make_api_request(url, params)
        
        # Process the API response into a standardized format
        weather_data = {
            "current": {
                # Create a simplified current weather section
                "temperature": {
                    "value": response.get("daily", {}).get("temperature_2m_max", [None])[0],
                    "unit": "°C"
                },
                "humidity": {"value": None, "unit": "%"},  # Not directly available in this API
                "wind_speed": {
                    "value": response.get("daily", {}).get("wind_speed_10m_max", [None])[0],
                    "unit": "km/h"
                },
                "rainfall": {
                    "value": response.get("daily", {}).get("rain_sum", [None])[0],
                    "unit": "mm"
                },
                "time": datetime.now().isoformat()
            },
            "forecast": {
                "daily": []
            }
        }
        
        # Process daily forecast
        daily_data = response.get("daily", {})
        days = len(daily_data.get("time", []))
        
        for i in range(days):
            day_data = {
                "date": daily_data.get("time", [])[i],
                "temp_max": {
                    "value": daily_data.get("temperature_2m_max", [])[i],
                    "unit": "°C"
                },
                "temp_min": {
                    "value": daily_data.get("temperature_2m_min", [])[i],
                    "unit": "°C" 
                },
                "precipitation": {
                    "value": daily_data.get("precipitation_sum", [])[i],
                    "unit": "mm"
                },
                "wind_speed": {
                    "value": daily_data.get("wind_speed_10m_max", [])[i],
                    "unit": "km/h"
                }
            }
            weather_data["forecast"]["daily"].append(day_data)
            
        return weather_data
        
    except Exception as e:
        logger.error(f"Error getting weather data: {str(e)}")
        raise WeatherServiceError(f"Weather service unavailable: {str(e)}")
