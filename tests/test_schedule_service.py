import unittest
from datetime import datetime

from src.models import Course
from src.schedule_service import ScheduleService


class FakeProvider:
    @staticmethod
    def courses_for(_day):
        return [
            Course("08:00", "08:45", "Math", "M", "Alice"),
            Course("09:00", "09:45", "English", "E", "Bob"),
        ]


class ScheduleServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ScheduleService(FakeProvider())

    def test_current_course(self):
        data = self.service.build_canvas_data(
            "Owner", "Sunny", datetime(2026, 8, 10, 8, 15)
        )
        self.assertEqual(data["course"], "Math")
        self.assertEqual(data["remaining"], "30")
        self.assertEqual(data["progress"], "33")
        self.assertEqual(data["teacher"], "教师 Alice")

    def test_break_uses_next_course(self):
        data = self.service.build_canvas_data(
            "Owner", "Sunny", datetime(2026, 8, 10, 8, 50)
        )
        self.assertEqual(data["course"], "课间休息")
        self.assertIn("English", data["period"])
        self.assertEqual(data["remaining"], "10")

    def test_before_first_course(self):
        data = self.service.build_canvas_data(
            "Owner", "Sunny", datetime(2026, 8, 10, 7, 30)
        )
        self.assertEqual(data["course"], "Math")
        self.assertEqual(data["todayRemaining"], "2")

    def test_weather_is_omitted_when_unavailable(self):
        data = self.service.build_canvas_data(
            "Owner", None, datetime(2026, 8, 10, 8, 15)
        )
        self.assertNotIn("weather", data)


if __name__ == "__main__":
    unittest.main()
