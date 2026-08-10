import unittest

from src.weather import WeatherService


class FakeWeatherClient:
    def __init__(self):
        self.calls = 0

    def fetch(self, _location, _timeout_seconds):
        self.calls += 1
        return "Sunny"


class WeatherServiceTests(unittest.TestCase):
    def test_cache_avoids_duplicate_request(self):
        client = FakeWeatherClient()
        service = WeatherService(client=client, clock=lambda: 100)
        self.assertEqual(service.get("Hong Kong", 10), "Sunny")
        self.assertEqual(service.get("Hong Kong", 10), "Sunny")
        self.assertEqual(client.calls, 1)

    def test_empty_location_skips_client(self):
        client = FakeWeatherClient()
        service = WeatherService(client=client)
        self.assertIsNone(service.get("", 10))
        self.assertEqual(client.calls, 0)


if __name__ == "__main__":
    unittest.main()
