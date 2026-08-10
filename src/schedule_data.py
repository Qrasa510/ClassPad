"""Compatibility helpers for callers using the original schedule_data API."""

from src.cses_schedule import CsesScheduleProvider
from src.schedule_service import ScheduleService


def make_data(owner, weather, runtime_config, now=None):
    cses_file = getattr(runtime_config, "cses_file", None) or runtime_config["cses_file"]
    service = ScheduleService(CsesScheduleProvider(cses_file))
    return service.build_canvas_data(owner, weather, now=now)
