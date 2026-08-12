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
        self._active_target_keys = set()

    def run_once(self, config, should_continue=None) -> None:
        if should_continue is not None and not should_continue():
            return

        targets = self._target_loader(config.devices_file)
        active_keys = {target.key for target in targets}
        if active_keys != self._active_target_keys:
            device_names = "、".join(target.device_id for target in targets)
            logger.info("找到 %s 台设备 · %s", len(targets), device_names)
            self._active_target_keys = active_keys

        self._last_data_by_target = {
            key: data
            for key, data in self._last_data_by_target.items()
            if key in active_keys
        }

        for target in targets:
            if should_continue is not None and not should_continue():
                return

            weather = None
            if target.location:
                try:
                    weather = self._weather.get(
                        target.location, config.request_timeout_seconds
                    )
                except LocationError as exc:
                    logger.error(
                        "找不到「%s」的天气 · 设备 %s · %s",
                        target.location,
                        target.device_id,
                        exc,
                    )
                except WeatherError as exc:
                    logger.warning(
                        "天气暂时走丢了 · 设备 %s · %s · %s",
                        target.device_id,
                        target.location,
                        exc,
                    )

            if should_continue is not None and not should_continue():
                return

            data = self._schedule.build_canvas_data(target.owner, weather)
            if self._last_data_by_target.get(target.key) == data:
                logger.debug("内容没有变化 · 设备 %s，继续安静等待", target.device_id)
                continue

            if should_continue is not None and not should_continue():
                return

            try:
                self._canvas.push(target, data, config.request_timeout_seconds)
                self._last_data_by_target[target.key] = data
            except CanvasAuthError as exc:
                logger.error("设备 %s 没有通过认证 · %s", target.device_id, exc)
            except CanvasError as exc:
                logger.warning("设备 %s 暂时没收到更新 · %s", target.device_id, exc)
