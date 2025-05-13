/**
 * @file Weather.jsx
 * @description A React component that displays weather information and provides gardening advice based on the current weather conditions.
 * 
 * @param {Object} props - The component props.
 * @param {Object} props.weather - The weather data object.
 * @param {string} props.weather.name - The name of the location.
 * @param {Object[]} props.weather.weather - Array containing weather condition details.
 * @param {string} props.weather.weather[0].icon - The icon code for the current weather condition.
 * @param {string} props.weather.weather[0].description - A textual description of the current weather condition.
 * @param {Object} props.weather.main - Main weather details.
 * @param {number} props.weather.main.temp - The current temperature in Celsius.
 * @param {number} props.weather.main.humidity - The current humidity percentage.
 * @param {Object} [props.weather.rain] - Rain data (optional).
 * @param {number} [props.weather.rain["1h"]] - Rain volume for the last hour in mm (optional).
 * 
 * @returns {JSX.Element} A styled weather card with location, weather details, and gardening advice.
 */
import './styles/weather.css';

const Weather = ({ weather }) => {
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
              <p>{weather.rain.oneHour} mm/h</p>
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

export default Weather;
