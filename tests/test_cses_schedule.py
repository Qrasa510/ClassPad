import tempfile
import unittest
from pathlib import Path

from src.config_store import load_runtime_config
from src.cses_schedule import CsesScheduleProvider
from src.schedule_service import ScheduleService


class CsesScheduleTests(unittest.TestCase):
    def test_invalid_cses_is_rejected_during_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text("not: a valid cses file\n", encoding="utf-8")
            with self.assertRaises((ValueError, KeyError)):
                CsesScheduleProvider(path).validate()

    def test_project_configuration_builds_canvas_data(self):
        config = load_runtime_config()
        provider = CsesScheduleProvider(config.cses_file)
        provider.validate()
        data = ScheduleService(provider).build_canvas_data("Test", None)
        self.assertEqual(data["owner"], "Test")
        self.assertIn("course", data)
        self.assertIn("progress", data)


if __name__ == "__main__":
    unittest.main()
