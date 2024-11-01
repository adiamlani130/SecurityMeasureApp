#install necessary libraries and packages
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
#getWeatherSummary calls Open-Meteo API to recieve location information
def getWeatherSummary(call):   
   # Setup the Open-Meteo API client with cache and retry on error
   cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
   retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
   openmeteo = openmeteo_requests.Client(session = retry_session)
   #Message to be displayed on homescreen, and to be sent to user's mobile device
   #snsMessage is condensed version fo fullMessage
   snsMessage=""
   fullMessage=""
   # Make sure all required weather variables are listed here
   # The order of variables in hourly or daily is important to assign them correctly below
   url = "https://api.open-meteo.com/v1/forecast"
   params = {
       "latitude": 52.52,
       "longitude": 13.41,
       "current": ["temperature_2m", "precipitation", "weather_code", "wind_speed_10m"],
       "hourly": ["temperature_2m", "precipitation_probability", "rain", "showers", "snowfall", "uv_index"],
       "daily": ["uv_index_max", "precipitation_sum", "wind_speed_10m_max"],
       "temperature_unit": "fahrenheit",
       "wind_speed_unit": "mph",
       "precipitation_unit": "inch",
       "timezone": "America/New_York"
   }
   responses = openmeteo.weather_api(url, params=params)
   # Process first location. Add a for-loop for multiple locations or weather models
   response = responses[0]
   #Add to sns message
   snsMessage+=(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
   snsMessage+=(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
   fullMessage+=snsMessage
   fullMessage+=(f"Elevation {response.Elevation()} m asl")
   # Current values. The order of variables needs to be the same as requested.
   current = response.Current()
   current_temperature_2m = current.Variables(0).Value()
   current_precipitation = current.Variables(1).Value()
   current_weather_code = current.Variables(2).Value()
   current_wind_speed_10m = current.Variables(3).Value()
   #add to sns messgae
   snsMessage+=(f"Current temperature_2m {current_temperature_2m}")
   snsMessage+=(f"Current precipitation {current_precipitation}")
   snsMessage+=(f"Current weather_code {current_weather_code}")
   snsMessage+=(f"Current wind_speed_10m {current_wind_speed_10m}")
   fullMessage+=snsMessage
   # Process hourly data. The order of variables needs to be the same as requested.
   hourly = response.Hourly()
   hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
   hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
   hourly_rain = hourly.Variables(2).ValuesAsNumpy()
   hourly_showers = hourly.Variables(3).ValuesAsNumpy()
   hourly_snowfall = hourly.Variables(4).ValuesAsNumpy()
   hourly_uv_index = hourly.Variables(5).ValuesAsNumpy()
   #Take data every hour
   hourly_data = {"date": pd.date_range(
       start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
       end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
       freq = pd.Timedelta(seconds = hourly.Interval()),
       inclusive = "left"
   )}
   hourly_data["temperature_2m"] = hourly_temperature_2m
   hourly_data["precipitation_probability"] = hourly_precipitation_probability
   hourly_data["rain"] = hourly_rain
   hourly_data["showers"] = hourly_showers
   hourly_data["snowfall"] = hourly_snowfall
   hourly_data["uv_index"] = hourly_uv_index
   #Add hourly data to full message
   fullMessage+=pd.DataFrame(data = hourly_data)
   print(fullMessage)
   # Process daily data. The order of variables needs to be the same as requested.
   daily = response.Daily()
   daily_uv_index_max = daily.Variables(0).ValuesAsNumpy()
   daily_precipitation_sum = daily.Variables(1).ValuesAsNumpy()
   daily_wind_speed_10m_max = daily.Variables(2).ValuesAsNumpy()
   # Take data every day
   daily_data = {"date": pd.date_range(
       start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
       end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
       freq = pd.Timedelta(seconds = daily.Interval()),
       inclusive = "left"
   )}
   daily_data["uv_index_max"] = daily_uv_index_max
   daily_data["precipitation_sum"] = daily_precipitation_sum
   daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
   # Add daily data to full message
   fullMessage += pd.DataFrame(data = daily_data)
   print(fullMessage)
   #Return message for GUI frontpage summary or to be sent to user through sns
   if(call):
       return snsMessage
   else:
       return fullMessage
