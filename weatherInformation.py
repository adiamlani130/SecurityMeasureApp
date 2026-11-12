#install necessary libraries and packages
import requests_cache
from retry_requests import retry
import config

URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes used by Open-Meteo
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light rain showers", 81: "Rain showers", 82: "Violent rain showers",
    85: "Light snow showers", 86: "Snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

_session = None


#Format a number that Open-Meteo may return as null
def _fmt(value, digits=0):
    return "?" if value is None else f"{value:.{digits}f}"


#Open-Meteo session with a 1 hour cache and retry on error
def _getSession():
    global _session
    if _session is None:
        cacheSession = requests_cache.CachedSession('.weather_cache', expire_after=3600)
        _session = retry(cacheSession, retries=5, backoff_factor=0.2)
    return _session


#Fetch the raw forecast JSON from Open-Meteo
def fetchWeather():
    params = {
        "latitude": config.LATITUDE,
        "longitude": config.LONGITUDE,
        "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                 "precipitation_sum,uv_index_max,wind_speed_10m_max",
        "forecast_days": 1,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": config.TIMEZONE,
    }
    response = _getSession().get(URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


#Turn the forecast JSON into text. call=True gives the short SMS version, False the GUI version
def formatWeather(data, call):
    current = data["current"]
    daily = data["daily"]
    condition = WEATHER_CODES.get(current["weather_code"], f"Code {current['weather_code']}")
    snsMessage = (f"Weather: {condition}, {_fmt(current['temperature_2m'], 0)}°F, "
                  f"wind {_fmt(current['wind_speed_10m'], 0)} mph, "
                  f"precip {_fmt(current['precipitation'], 2)} in")
    if call:
        return snsMessage
    fullMessage = (
        f"{condition}\n"
        f"Now: {_fmt(current['temperature_2m'], 0)}°F, wind {_fmt(current['wind_speed_10m'], 0)} mph\n"
        f"Today: high {_fmt(daily['temperature_2m_max'][0], 0)}°F / low {_fmt(daily['temperature_2m_min'][0], 0)}°F\n"
        f"Rain chance {_fmt(daily['precipitation_probability_max'][0], 0)}%, "
        f"total {_fmt(daily['precipitation_sum'][0], 2)} in\n"
        f"Max UV {_fmt(daily['uv_index_max'][0], 1)}, max wind {_fmt(daily['wind_speed_10m_max'][0], 0)} mph"
    )
    return fullMessage


#getWeatherSummary calls Open-Meteo API to receive local weather information
def getWeatherSummary(call):
    return formatWeather(fetchWeather(), call)
