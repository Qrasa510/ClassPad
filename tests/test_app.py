import unittest
from pathlib import Path

from src.app import ClassPadApp
from src.models import PushTarget, RuntimeConfig


class FakeCanvas:
    def __init__(self):
        self.calls = []

    def push(self, target, data, timeout):
        self.calls.append((target, data, timeout))


class FakeWeather:
    def get(self, location, timeout):
        return "Live weather"


class FakeSchedule:
    def build_canvas_data(self, owner, weather):
        return {"owner": owner, "weather": weather}


class AppTests(unittest.TestCase):
    def test_unchanged_payload_is_not_pushed_twice(self):
        target = PushTarget("token", "device", "Owner", "Hong Kong")
        canvas = FakeCanvas()
        app = ClassPadApp(
            canvas,
            FakeWeather(),
            FakeSchedule(),
            target_loader=lambda _: [target],
        )
        config = RuntimeConfig(30, 15, Path("devices"), Path("schedule"))

        app.run_once(config)
        app.run_once(config)

        self.assertEqual(len(canvas.calls), 1)
        self.assertEqual(canvas.calls[0][1]["weather"], "Live weather")


if __name__ == "__main__":
    unittest.main()
