import './styles/weather.css';
import React, { useEffect } from 'react';

import { useUser } from '../../hooks';

const WeatherWidget = () => {
  // Move later
  const API_KEY = "ff501ab5606085a5564e2ee89a2856f2";

  React.useEffect(() => {
    const fetchWeather = async () => {
      try {
        const response = await fetch(`http://api.openweathermap.org/data/2.5/weather?q=London&appid=${API_KEY}&units=metric`);
        if (!response.ok) {
          throw new Error("Failed to fetch weather data");
        }
        const data = await response.json();
        setWeather(data);
      } catch (error) {
        console.error("Error fetching weather data:", error);
      }
    };

    fetchWeather();
  }, []);

  if (!weather) {
    return (
      <div className="loading">
        <p>Loading weather...</p>
      </div>
    );
  }

  const iconUrl = `http://openweathermap.org/img/wn/${weather.weather[0].icon}@2x.png`;

  const getGardeningAdvice = () => {
    const temp = weather.main.temp;
    const humidity = weather.main.humidity;
    const description = weather.weather[0].description.toLowerCase();

    if (description.includes("rain")) {
      return {
        text: "Avoid planting; soil may be too wet. Consider indoor tasks.",
        color: "color: #2563eb;",
      };
    }
    if (temp < 5) {
      return {
        text: "Too cold for most planting. Protect sensitive plants.",
        color: "color: #dc2626;",
      };
    }
    if (temp > 30) {
      return {
        text: "Water plants frequently; avoid midday heat.",
        color: "color: #ea580c;",
      };
    }
    if (humidity < 30) {
      return {
        text: "Low humidity; ensure soil stays moist.",
        color: "color: #ca8a04;",
      };
    }
    return {
      text: "Good conditions for gardening! Check soil moisture.",
      color: "color: #16a34a;",
    };
  };

  const gardeningAdvice = getGardeningAdvice();

  return (
    <div className="weather-card">
      <div className="header">
        <div className="header-content">
          <h2>{weather.name}</h2>
          <img
            src={iconUrl}
            alt={weather.weather[0].description}
          />
        </div>
        <p>{weather.weather[0].description}</p>
      </div>

      <div className="details">
        <div className="detail-item">
          <span>🌡️</span>
          <div>
            <p>Temperature</p>
            <p>{weather.main.temp}°C</p>
          </div>
        </div>
        <div className="detail-item">
          <span>💧</span>
          <div>
            <p>Humidity</p>
            <p>{weather.main.humidity}%</p>
          </div>
        </div>
        {weather.rain && weather.rain["1h"] && (
          <div className="detail-item full-width">
            <span>🌧️</span>
            <div>
              <p>Rain</p>
              <p>{weather.rain["1h"]} mm/h</p>
            </div>
          </div>
        )}
      </div>

      <div className="advice">
        <p style={{ color: gardeningAdvice.color.split(': ')[1].replace(';', '') }}>
          🌱 <span>Gardening Tip:</span> {gardeningAdvice.text}
        </p>
      </div>
    </div>
  );
};

export default WeatherWidget;