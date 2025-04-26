# backend/root/services/tests/test_weather_service.py

import unittest
import json
import time
import requests
from unittest.mock import patch, MagicMock

from services.weather_service import (
    get_coordinates_from_zip,
    get_coordinates_from_place,
    get_current_weather,
    get_daily_forecast,
    get_garden_weather_insights,
    _calculate_watering_advice,
    _check_for_frost,
    _check_for_extreme_heat,
    _check_for_high_winds,
    _generate_forecast_summary,
    WeatherServiceError,
    _make_api_request,
    _weather_cache,
    _geocode_cache
)

class WeatherServiceTestCase(unittest.TestCase):
    
    def setUp(self):
        # Clear caches before each test
        _weather_cache.clear()
        _geocode_cache.clear()
        
        # Set up sample API responses
        self.zip_geocode_response = [
            {
                "place_id": 12345,
                "lat": "37.7749",
                "lon": "-122.4194", 
                "display_name": "San Francisco, CA 94103, USA"
            }
        ]
        
        self.place_geocode_response = {
            "results": [
                {
                    "id": 12345,
                    "name": "San Francisco",
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "country": "United States",
                    "admin1": "California"
                }
            ]
        }
        
        self.current_weather_response = {
            "latitude": 37.77,
            "longitude": -122.42,
            "timezone": "America/Los_Angeles",
            "current": {
                "time": "2025-04-24T12:00",
                "temperature_2m": 18.5,
                "relative_humidity_2m": 65,
                "rain": 0,
                "snowfall": 0,
                "cloud_cover": 25,
                "wind_speed_10m": 15,
                "wind_direction_10m": 270
            },
            "current_units": {
                "temperature_2m": "°C",
                "relative_humidity_2m": "%",
                "rain": "mm",
                "snowfall": "cm",
                "cloud_cover": "%", 
                "wind_speed_10m": "km/h",
                "wind_direction_10m": "°"
            }
        }
        
        self.daily_forecast_response = {
            "latitude": 37.77,
            "longitude": -122.42,
            "timezone": "America/Los_Angeles",
            "daily": {
                "time": ["2025-04-24", "2025-04-25", "2025-04-26"],
                "temperature_2m_max": [22.5, 24.0, 23.0],
                "temperature_2m_min": [14.0, 15.5, 14.8],
                "precipitation_sum": [0, 5.2, 1.0],
                "rain_sum": [0, 5.2, 1.0],
                "snowfall_sum": [0, 0, 0],
                "precipitation_hours": [0, 4, 1],
                "precipitation_probability_max": [0, 80, 30],
                "wind_speed_10m_max": [15, 22, 18],
                "wind_gusts_10m_max": [25, 35, 28],
                "sunshine_duration": [10, 4, 7],
                "uv_index_max": [7, 4, 6],
                "soil_temperature_0cm": [18, 17, 17.5]
            },
            "daily_units": {
                "temperature_2m_max": "°C",
                "temperature_2m_min": "°C",
                "precipitation_sum": "mm",
                "rain_sum": "mm",
                "snowfall_sum": "cm",
                "precipitation_hours": "h",
                "precipitation_probability_max": "%",
                "wind_speed_10m_max": "km/h",
                "wind_gusts_10m_max": "km/h", 
                "sunshine_duration": "h",
                "uv_index_max": "",
                "soil_temperature_0cm": "°C"
            }
        }
    
    def test_make_api_request_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        
        with patch('requests.get', return_value=mock_response):
            result = _make_api_request("http://test.url", {})
            self.assertEqual(result, {"data": "success"})
    
    def test_make_api_request_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error: 404")
        
        with patch('requests.get', return_value=mock_response):
            with self.assertRaises(WeatherServiceError):
                _make_api_request("http://test.url", {})
    
    def test_make_api_request_server_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error: 500")
        
        with patch('requests.get', return_value=mock_response):
            with self.assertRaises(WeatherServiceError):
                _make_api_request("http://test.url", {})
    
    def test_get_coordinates_from_zip(self):
        with patch('services.weather_service._make_api_request') as mock_api:
            mock_api.return_value = self.zip_geocode_response
            lat, lon = get_coordinates_from_zip("94103")
            
            # Verify results
            self.assertEqual(lat, 37.7749)
            self.assertEqual(lon, -122.4194)
            
            # Test caching
            mock_api.reset_mock()
            lat2, lon2 = get_coordinates_from_zip("94103")
            self.assertEqual(lat2, 37.7749)
            self.assertEqual(lon2, -122.4194)
            mock_api.assert_not_called()
    
    def test_get_coordinates_from_place(self):
        with patch('services.weather_service._make_api_request') as mock_api:
            mock_api.return_value = self.place_geocode_response
            lat, lon = get_coordinates_from_place("San Francisco")
            
            # Verify results
            self.assertEqual(lat, 37.7749)
            self.assertEqual(lon, -122.4194)
    
    def test_get_coordinates_from_place_not_found(self):
        with patch('services.weather_service._make_api_request') as mock_api:
            mock_api.return_value = {"results": []}  # Empty results
            
            with self.assertRaises(WeatherServiceError):
                get_coordinates_from_place("NonexistentPlace")
    
    def test_get_current_weather(self):
        lat, lon = 37.7749, -122.4194
        
        with patch('services.weather_service._make_api_request') as mock_api:
            mock_api.return_value = self.current_weather_response
            result = get_current_weather(lat, lon)
            
            # Verify structure and values
            self.assertIn("temperature", result)
            self.assertIn("value", result["temperature"])
            self.assertEqual(result["temperature"]["value"], 18.5)
            self.assertEqual(result["temperature"]["unit"], "°C")
            
            self.assertIn("humidity", result)
            self.assertEqual(result["humidity"]["value"], 65)
            
            self.assertIn("rain", result)
            self.assertEqual(result["rain"]["value"], 0)
            
            # Test caching
            mock_api.reset_mock()
            result2 = get_current_weather(lat, lon)
            self.assertEqual(result2, result)
            mock_api.assert_not_called()
    
    def test_get_daily_forecast(self):
        lat, lon = 37.7749, -122.4194
        
        with patch('services.weather_service._make_api_request') as mock_api:
            mock_api.return_value = self.daily_forecast_response
            result = get_daily_forecast(lat, lon)
            
            # Verify structure and values
            self.assertIn("daily", result)
            self.assertEqual(len(result["daily"]), 3)  # Three days from fixture
            
            day1 = result["daily"][0]
            self.assertEqual(day1["date"], "2025-04-24")
            self.assertEqual(day1["temperature"]["max"]["value"], 22.5)
            self.assertEqual(day1["precipitation"]["rain"]["value"], 0)
            
            # Verify the windy day
            day2 = result["daily"][1]
            self.assertEqual(day2["wind"]["speed"]["value"], 22)
    
    def test_calculate_watering_advice_recent_rain(self):
        # Test case: Recent rain, shouldn't need to water
        current_with_rain = {
            "rain": {"value": 5.0}
        }
        result = _calculate_watering_advice(current_with_rain, {"daily": []})
        self.assertFalse(result["should_water"])
        self.assertIn("Recent rainfall", result["reason"])
    
    def test_calculate_watering_advice_rain_coming(self):
        # Test case: No recent rain but rain coming soon
        current_no_rain = {
            "rain": {"value": 0},
            "temperature": {"value": 25},
            "humidity": {"value": 40}
        }
        forecast_with_rain = {
            "daily": [
                {
                    "precipitation": {
                        "rain": {"value": 10},
                        "probability": 80
                    },
                    "date": "2025-04-25"
                }
            ]
        }
        result = _calculate_watering_advice(current_no_rain, forecast_with_rain)
        self.assertFalse(result["should_water"])
        self.assertIn("Rain forecasted", result["reason"])
        self.assertEqual(result["next_rain_forecast"], "2025-04-25")
    
    def test_calculate_watering_advice_dry_conditions(self):
        # Test case: No rain, very dry conditions
        current_hot = {
            "rain": {"value": 0},
            "temperature": {"value": 50},
            "humidity": {"value": 5}
        }
        forecast_no_rain = {
            "daily": [
                {
                    "precipitation": {"rain": {"value": 0}},
                    "date": "2025-04-25"
                }
            ]
        }
        result = _calculate_watering_advice(current_hot, forecast_no_rain)
        self.assertTrue(result["should_water"])
        self.assertIn("Very dry conditions", result["reason"])
    
    def test_check_for_frost_with_frost(self):
        # Test case with frost
        forecast_with_frost = {
            "daily": [
                {
                    "date": "2025-04-24",
                    "temperature": {"min": {"value": 5}}
                },
                {
                    "date": "2025-04-25",
                    "temperature": {"min": {"value": -2}}
                }
            ]
        }
        result = _check_for_frost(forecast_with_frost)
        self.assertTrue(result["frost_risk"])
        self.assertEqual(len(result["frost_days"]), 1)
        self.assertEqual(result["min_temperature"], -2)
    
    def test_check_for_frost_no_frost(self):
        # Test case without frost
        forecast_no_frost = {
            "daily": [
                {
                    "date": "2025-04-24",
                    "temperature": {"min": {"value": 5}}
                }
            ]
        }
        result = _check_for_frost(forecast_no_frost)
        self.assertFalse(result["frost_risk"])
        self.assertEqual(len(result["frost_days"]), 0)
    
    def test_check_for_extreme_heat(self):
        # Test case with extreme heat
        forecast_with_heat = {
            "daily": [
                {
                    "date": "2025-04-24",
                    "temperature": {"max": {"value": 25}}
                },
                {
                    "date": "2025-04-25",
                    "temperature": {"max": {"value": 35}}
                }
            ]
        }
        result = _check_for_extreme_heat(forecast_with_heat)
        self.assertTrue(result["extreme_heat"])
        self.assertEqual(len(result["hot_days"]), 1)
        self.assertEqual(result["max_temperature"], 35)
    
    def test_check_for_high_winds(self):
        # Test case with high winds
        forecast_with_winds = {
            "daily": [
                {
                    "date": "2025-04-24",
                    "wind": {"speed": {"value": 15}, "gusts": {"value": 20}}
                },
                {
                    "date": "2025-04-25",
                    "wind": {"speed": {"value": 25}, "gusts": {"value": 40}}
                }
            ]
        }
        result = _check_for_high_winds(forecast_with_winds)
        self.assertTrue(result["high_winds"])
        self.assertEqual(len(result["windy_days"]), 1)
        self.assertEqual(result["max_wind_speed"], 25)
    
    def test_get_garden_weather_insights(self):
        # Setup mocks
        with patch('services.weather_service.get_coordinates_from_zip') as mock_coords:
            with patch('services.weather_service.get_current_weather') as mock_current:
                with patch('services.weather_service.get_daily_forecast') as mock_forecast:
                    # Configure mocks
                    mock_coords.return_value = (37.7749, -122.4194)
                    
                    mock_current.return_value = {
                        "temperature": {"value": 22, "unit": "°C"},
                        "humidity": {"value": 60, "unit": "%"},
                        "rain": {"value": 0, "unit": "mm"}
                    }
                    
                    mock_forecast.return_value = {
                        "timezone": "America/Los_Angeles",
                        "daily": [
                            {
                                "date": "2025-04-24",
                                "temperature": {
                                    "max": {"value": 25, "unit": "°C"},
                                    "min": {"value": 15, "unit": "°C"}
                                },
                                "precipitation": {
                                    "rain": {"value": 0, "unit": "mm"},
                                    "sum": {"value": 0, "unit": "mm"},
                                    "snowfall": {"value": 0, "unit": "cm"},
                                    "hours": 0,
                                    "probability": 5
                                },
                                "wind": {
                                    "speed": {"value": 15, "unit": "km/h"},
                                    "gusts": {"value": 25, "unit": "km/h"}
                                }
                            }
                        ]
                    }
                    
                    # Call function
                    result = get_garden_weather_insights("94103")
                    
                    # Verify all components were called and insights were generated
                    mock_coords.assert_called_once_with("94103")
                    mock_current.assert_called_once_with(37.7749, -122.4194)
                    mock_forecast.assert_called_once_with(37.7749, -122.4194, days=7)
                    
                    self.assertIn("watering_needed", result)
                    self.assertIn("frost_warning", result)
                    self.assertIn("extreme_heat_warning", result)
                    self.assertIn("high_wind_warning", result)
                    self.assertIn("forecast_summary", result)


if __name__ == "__main__":
    unittest.main()