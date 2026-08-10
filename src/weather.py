import time

import requests

from src.http_client import create_retry_session


GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE_SECONDS = 600

WEATHER_CODE_TO_EMOJI = {
    0: "☀", 1: "🌤", 2: "⛅", 3: "☁", 45: "🌫", 48: "🌫",
    51: "🌦", 53: "🌦", 55: "🌧", 56: "🌨", 57: "🌨",
    61: "🌦", 63: "🌧", 65: "🌧", 66: "🌨", 67: "🌨",
    71: "🌨", 73: "❄", 75: "❄", 77: "🌨", 80: "🌦",
    81: "🌧", 82: "🌧", 85: "🌨", 86: "❄", 95: "⛈",
    96: "⛈", 99: "⛈",
}


class WeatherError(RuntimeError):
    pass


class LocationError(WeatherError):
    pass


class OpenMeteoClient:
    def __init__(self, session=None):
        self._session = session or create_retry_session()

    def fetch(self, location: str, timeout_seconds: int) -> str:
        try:
            geo_response = self._session.get(
                GEOCODING_API_URL,
                params={"name": location, "count": 1, "language": "en", "format": "json"},
                timeout=timeout_seconds,
            )
            geo_response.raise_for_status()
            results = geo_response.json().get("results") or []
            if not results:
                raise LocationError(f"找不到城市: {location}")

            latitude = results[0].get("latitude")
            longitude = results[0].get("longitude")
            if latitude is None or longitude is None:
                raise LocationError(f"城市坐标无效: {location}")

            weather_response = self._session.get(
                FORECAST_API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,weather_code",
                    "timezone": "auto",
                },
                timeout=timeout_seconds,
            )
            weather_response.raise_for_status()
            current = weather_response.json().get("current") or {}
            temperature = current.get("temperature_2m")
            weather_code = current.get("weather_code")
            if temperature is None or weather_code is None:
                raise WeatherError(f"城市天气数据不完整: {location}")
        except WeatherError:
            raise
        except requests.RequestException as exc:
            raise WeatherError(f"天气请求失败: {exc}") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise WeatherError(f"天气数据解析失败: {location}") from exc

        emoji = WEATHER_CODE_TO_EMOJI.get(int(weather_code), "🌡")
        return f"{emoji} {int(round(float(temperature)))}°C"


class WeatherService:
    def __init__(self, client=None, cache_seconds=WEATHER_CACHE_SECONDS, clock=None):
        self._client = client or OpenMeteoClient()
        self._cache_seconds = cache_seconds
        self._clock = clock or time.time
        self._cache = {}

    def get(self, location: str, timeout_seconds: int) -> str | None:
        if not location:
            return None
        now = self._clock()
        cached = self._cache.get(location)
        if cached and now - cached["at"] < self._cache_seconds:
            return cached["weather"]
        weather = self._client.fetch(location, timeout_seconds)
        self._cache[location] = {"weather": weather, "at": now}
        return weather
