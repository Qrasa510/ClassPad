import logging

from src.canvas_client import CanvasAuthError, CanvasError
from src.config_store import load_push_targets
from src.weather import LocationError, WeatherError


logger = logging.getLogger(__name__)


class ClassPadApp:
    def __init__(self, canvas_client, weather_service, schedule_service, target_loader=None):
        self._canvas = canvas_client
        self._weather = weather_service
        self._schedule = schedule_service
        self._target_loader = target_loader or load_push_targets
        self._last_data_by_target = {}

    def run_once(self, config) -> None:
        targets = self._target_loader(config.devices_file)
        active_keys = {target.key for target in targets}
        self._last_data_by_target = {
            key: data
            for key, data in self._last_data_by_target.items()
            if key in active_keys
        }

        for target in targets:
            weather = None
            if target.location:
                try:
                    weather = self._weather.get(
                        target.location, config.request_timeout_seconds
                    )
                except LocationError as exc:
                    logger.error(
                        "设备天气位置无效 device=%s location=%s error=%s",
                        target.device_id,
                        target.location,
                        exc,
                    )
                except WeatherError as exc:
                    logger.warning(
                        "设备天气暂时不可用 device=%s location=%s error=%s",
                        target.device_id,
                        target.location,
                        exc,
                    )

            data = self._schedule.build_canvas_data(target.owner, weather)
            if self._last_data_by_target.get(target.key) == data:
                logger.debug("设备显示数据未变化 device=%s", target.device_id)
                continue

            try:
                self._canvas.push(target, data, config.request_timeout_seconds)
                self._last_data_by_target[target.key] = data
            except CanvasAuthError as exc:
                logger.error("设备认证失败 device=%s error=%s", target.device_id, exc)
            except CanvasError as exc:
                logger.warning("设备推送暂时失败 device=%s error=%s", target.device_id, exc)
