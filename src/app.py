from src.config_store import load_push_targets


class ClassPadApp:
    def __init__(self, canvas_client, weather_service, schedule_service, target_loader=None):
        self._canvas = canvas_client
        self._weather = weather_service
        self._schedule = schedule_service
        self._target_loader = target_loader or load_push_targets
        self._last_data_by_target = {}

    def run_once(self, config) -> None:
        targets = self._target_loader(config.devices_file)
        if not targets:
            print(f"No push targets found, check {config.devices_file}")
            return

        for target in targets:
            weather = None
            if target.location:
                try:
                    weather = self._weather.get(target.location, config.request_timeout_seconds)
                except Exception as exc:
                    print(f"Weather failed [{target.device_id}] ({target.location}):", exc)

            data = self._schedule.build_canvas_data(target.owner, weather)
            if self._last_data_by_target.get(target.key) == data:
                continue

            try:
                self._canvas.push(target, data, config.request_timeout_seconds)
                self._last_data_by_target[target.key] = data
            except Exception as exc:
                print(f"Push failed [{target.device_id}]:", exc)
