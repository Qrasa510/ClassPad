import tempfile
import unittest
from pathlib import Path

from src.config_store import load_runtime_config
from src.cses_schedule import CsesScheduleProvider, CsesValidationError
from src.schedule_service import ScheduleService

from lib.pycses.cses.generator import CSESGenerator
from lib.pycses.cses.parser import CSESParser


class CsesScheduleTests(unittest.TestCase):
    def test_generator_time_normalizer_is_static(self):
        self.assertEqual(CSESGenerator._normalize_time("8:05"), "08:05:00")

    def test_parser_file_check_handles_invalid_yaml_types(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text("123\n", encoding="utf-8")
            self.assertFalse(CSESParser.is_cses_file(str(path)))

    def test_invalid_cses_is_rejected_during_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text("not: a valid cses file\n", encoding="utf-8")
            with self.assertRaises(CsesValidationError):
                CsesScheduleProvider(path).validate()

    def test_unquoted_yaml_times_after_nine_are_not_dropped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "standard.yaml"
            path.write_text(
                """version: 1
subjects:
  - name: 生物
  - name: 数学
schedules:
  - name: Wednesday
    enable_day: 3
    weeks: all
    classes:
      - subject: 生物
        start_time: 09:10:00
        end_time: 09:50:00
      - subject: 数学
        start_time: 10:00:00
        end_time: 10:40:00
""",
                encoding="utf-8",
            )

            courses = CsesScheduleProvider(path).courses_for("WED")

            self.assertEqual([course.name for course in courses], ["生物", "数学"])
            self.assertEqual(courses[1].start, "10:00")
            self.assertEqual(courses[1].end, "10:40")

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
