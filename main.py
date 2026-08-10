import time

from src.app import ClassPadApp
from src.canvas_client import CanvasClient
from src.config_store import DEFAULT_CONFIG_FILE, load_runtime_config
from src.cses_schedule import CsesScheduleProvider
from src.schedule_service import ScheduleService
from src.weather import WeatherService


def main():
    app = None
    schedule_path = None
    sleep_seconds = 30

    while True:
        try:
            config = load_runtime_config(DEFAULT_CONFIG_FILE)
            sleep_seconds = config.push_interval_seconds

            if app is None or schedule_path != config.cses_file:
                schedule_path = config.cses_file
                app = ClassPadApp(
                    canvas_client=CanvasClient(),
                    weather_service=WeatherService(),
                    schedule_service=ScheduleService(CsesScheduleProvider(schedule_path)),
                )

            app.run_once(config)
        except Exception as exc:
            print("Push loop failed:", exc)

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
