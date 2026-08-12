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
    @staticmethod
    def get(_location, _timeout):
        return "Live weather"


class FakeSchedule:
    @staticmethod
    def build_canvas_data(owner, weather):
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

    def test_removed_target_is_pruned_from_dedupe_cache(self):
        first = PushTarget("token", "first", "Owner")
        second = PushTarget("token", "second", "Owner")
        current_targets = [first, second]
        app = ClassPadApp(
            FakeCanvas(),
            FakeWeather(),
            FakeSchedule(),
            target_loader=lambda _: current_targets,
        )
        config = RuntimeConfig(30, 15, Path("devices"), Path("schedule"))

        app.run_once(config)
        current_targets.remove(first)
        app.run_once(config)

        self.assertNotIn(first.key, app._last_data_by_target)
        self.assertIn(second.key, app._last_data_by_target)

    def test_cancelled_cycle_does_not_push(self):
        target = PushTarget("token", "device", "Owner", "Hong Kong")
        canvas = FakeCanvas()
        app = ClassPadApp(
            canvas,
            FakeWeather(),
            FakeSchedule(),
            target_loader=lambda _: [target],
        )
        config = RuntimeConfig(30, 15, Path("devices"), Path("schedule"))

        app.run_once(config, should_continue=lambda: False)

        self.assertEqual([], canvas.calls)


if __name__ == "__main__":
    unittest.main()
