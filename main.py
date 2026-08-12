import logging
import threading

from src.app import ClassPadApp
from src.canvas_client import CanvasClient
from src.console import (
    COMMAND_PAUSE,
    COMMAND_RESTART,
    COMMAND_STOP,
    CONTROL_PAUSED,
    CONTROL_RELOADING,
    CONTROL_RUNNING,
    CONTROL_STOPPING,
    BottomCommandBar,
    ConsoleCommandReader,
    configure_logging,
    print_banner,
)
from src.config_store import ConfigError, DEFAULT_CONFIG_FILE, load_runtime_config
from src.cses_schedule import CsesScheduleProvider
from src.schedule_service import ScheduleService
from src.weather import WeatherService


logger = logging.getLogger(__name__)


class RuntimeControl:
    def __init__(self, command_bar: BottomCommandBar):
        self._command_bar = command_bar
        self._condition = threading.Condition()
        self._paused = False
        self._restart_requested = False
        self._stop_requested = False

    @property
    def paused(self) -> bool:
        with self._condition:
            return self._paused

    @property
    def stop_requested(self) -> bool:
        with self._condition:
            return self._stop_requested

    def can_push(self) -> bool:
        with self._condition:
            return not (
                self._paused
                or self._restart_requested
                or self._stop_requested
            )

    def handle(self, command: str) -> None:
        status = CONTROL_RUNNING
        message = None
        with self._condition:
            if self._stop_requested:
                return
            if command == COMMAND_PAUSE:
                self._paused = not self._paused
                if self._paused:
                    status = CONTROL_PAUSED
                    message = "推送已暂停 · 按 p 随时继续"
                else:
                    message = "推送继续 · 正在看看课表有没有新变化"
            elif command == COMMAND_RESTART:
                self._restart_requested = True
                self._paused = False
                status = CONTROL_RELOADING
                message = "收到重载指令 · 正在重新读取配置和课表"
            elif command == COMMAND_STOP:
                self._stop_requested = True
                status = CONTROL_STOPPING
                message = "收到停止指令 · 正在收好课表"
            else:
                return
            self._condition.notify_all()

        self._command_bar.update(status)
        logger.info(message)

    def consume_restart(self) -> bool:
        with self._condition:
            if not self._restart_requested:
                return False
            self._restart_requested = False
            return True

    def mark_running(self) -> None:
        with self._condition:
            if self._stop_requested or self._restart_requested or self._paused:
                return
            self._command_bar.update(CONTROL_RUNNING)

    def mark_reloading(self) -> None:
        self._command_bar.update(CONTROL_RELOADING)

    def wait_for_action(self, timeout: float) -> None:
        with self._condition:
            if self._paused or self._restart_requested or self._stop_requested:
                return
            self._condition.wait_for(
                lambda: (
                    self._paused
                    or self._restart_requested
                    or self._stop_requested
                ),
                timeout=timeout,
            )

    def wait_while_paused(self) -> None:
        with self._condition:
            self._condition.wait_for(
                lambda: (
                    not self._paused
                    or self._restart_requested
                    or self._stop_requested
                )
            )


def main():
    command_bar = configure_logging()
    print_banner(command_bar.stream)
    control = RuntimeControl(command_bar)
    command_reader = ConsoleCommandReader(on_command=control.handle)
    if command_reader.start():
        command_bar.show()

    app = None
    schedule_path = None
    sleep_seconds = 30

    try:
        while not control.stop_requested:
            if control.consume_restart():
                app = None
                schedule_path = None
                control.mark_reloading()

            if control.paused:
                control.wait_while_paused()
                continue

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
                    logger.info(
                        "课表已经准备好 · %s · 每 %s 秒重新检查",
                        schedule_path.name,
                        sleep_seconds,
                    )

                app.run_once(config, should_continue=control.can_push)
                control.mark_running()
            except ConfigError as exc:
                logger.error("配置还没准备好 · %s", exc)
            except (OSError, ValueError, RuntimeError) as exc:
                logger.error("课表暂时无法读取 · %s", exc)

            control.wait_for_action(sleep_seconds)
    except KeyboardInterrupt:
        control.handle(COMMAND_STOP)
    finally:
        command_reader.stop()
        command_bar.hide()
        logger.info("ClassPad 已安静停下 · 晚点见")


if __name__ == "__main__":
    main()
