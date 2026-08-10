import logging
import time

from src.app import ClassPadApp
from src.canvas_client import CanvasClient
from src.config_store import ConfigError, DEFAULT_CONFIG_FILE, load_runtime_config
from src.cses_schedule import CsesScheduleProvider
from src.schedule_service import ScheduleService
from src.weather import WeatherService


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    configure_logging()
    app = None
    schedule_path = None
    sleep_seconds = 30

    while True:
        try:
            config = load_runtime_config(DEFAULT_CONFIG_FILE)
            sleep_seconds = config.push_interval_seconds

            if app is None or schedule_path != config.cses_file:
                provider = CsesScheduleProvider(config.cses_file)
                provider.validate()
                schedule_path = config.cses_file
                app = ClassPadApp(
                    canvas_client=CanvasClient(),
                    weather_service=WeatherService(),
                    schedule_service=ScheduleService(provider),
                )
                logger.info("配置加载成功 cses=%s", schedule_path)

            app.run_once(config)
        except ConfigError as exc:
            logger.error("配置错误: %s", exc)
        except (OSError, ValueError, RuntimeError) as exc:
            logger.error("课表加载失败: %s", exc)

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
