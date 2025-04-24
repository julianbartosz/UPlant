import React, { useEffect, useState } from "react";

const WeatherWidget = ({ zipcode = 53211 }) => {
  const [weather, setWeather] = useState(null);
  const API_KEY = "ff501ab5606085a5564e2ee89a2856f2";

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        const response = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?zip=${zipcode}&units=metric&appid=${API_KEY}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch weather data");
        }
        const data = await response.json();
        setWeather(data);
      } catch (err) {
        console.error("Failed to fetch weather:", err);
      }
    };

    fetchWeather();
  }, [zipcode]);

  if (!weather) {
    return (
      <div className="flex justify-center items-center h-48 bg-gray-100 rounded-xl shadow-md">
        <p className="text-gray-500">Loading weather...</p>
      </div>
    );
  }

  const iconUrl = `http://openweathermap.org/img/wn/${weather.weather[0].icon}@2x.png`;
  
  // Gardening-specific recommendations
  const getGardeningAdvice = () => {
    const temp = weather.main.temp;
    const humidity = weather.main.humidity;
    const description = weather.weather[0].description.toLowerCase();

    if (description.includes("rain")) {
      return {
        text: "Avoid planting; soil may be too wet. Consider indoor tasks.",
        color: "text-blue-600",
      };
    }
    if (temp < 5) {
      return {
        text: "Too cold for most planting. Protect sensitive plants.",
        color: "text-red-600",
      };
    }
    if (temp > 30) {
      return {
        text: "Water plants frequently; avoid midday heat.",
        color: "text-orange-600",
      };
    }
    if (humidity < 30) {
      return {
        text: "Low humidity; ensure soil stays moist.",
        color: "text-yellow-600",
      };
    }
    return {
      text: "Good conditions for gardening! Check soil moisture.",
      color: "text-green-600",
    };
  };

  const gardeningAdvice = getGardeningAdvice();

  return (
    <div className="p-6 bg-gradient-to-br from-green-50 to-blue-50 rounded-xl shadow-lg max-w-sm mx-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">{weather.name}</h2>
        <img
          src={iconUrl}
          alt={weather.weather[0].description}
          className="w-16 h-16"
        />
      </div>
      
      <div className="mt-4">
        <p className="text-lg capitalize text-gray-700">
          {weather.weather[0].description}
        </p>
        <div className="flex items-center space-x-2 mt-2">
          <span className="text-2xl">🌡️</span>
          <p className="text-xl font-medium text-gray-800">{weather.main.temp}°C</p>
        </div>
        <div className="flex items-center space-x-2 mt-2">
          <span className="text-2xl">💧</span>
          <p className="text-lg text-gray-700">Humidity: {weather.main.humidity}%</p>
        </div>
        {weather.rain && weather.rain["1h"] && (
          <div className="flex items-center space-x-2 mt-2">
            <span className="text-2xl">🌧️</span>
            <p className="text-lg text-gray-700">
              Rain: {weather.rain["1h"]} mm/h
            </p>
          </div>
        )}
      </div>

      <div className="mt-4 p-4 bg-white/50 rounded-lg">
        <p className={`text-sm font-medium ${gardeningAdvice.color}`}>
          🌱 Gardening Tip: {gardeningAdvice.text}
        </p>
      </div>
    </div>
  );
};

export default WeatherWidget;