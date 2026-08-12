import logging
import os
import queue
import shutil
import sys
import threading
import unicodedata
from textwrap import indent
from typing import Callable, TextIO


RESET = "\033[0m"
BOLD = "\033[1m"
MINT = "\033[38;5;114m"
SKY = "\033[38;5;117m"
WARM = "\033[38;5;222m"
ROSE = "\033[38;5;203m"
GRAY = "\033[38;5;245m"

LEVEL_STYLES = {
    logging.DEBUG: ("·", GRAY),
    logging.INFO: ("✦", MINT),
    logging.WARNING: ("☁", WARM),
    logging.ERROR: ("×", ROSE),
    logging.CRITICAL: ("×", ROSE),
}

COMMAND_PAUSE = "pause"
COMMAND_RESTART = "restart"
COMMAND_STOP = "stop"

CONTROL_RUNNING = "running"
CONTROL_PAUSED = "paused"
CONTROL_RELOADING = "reloading"
CONTROL_STOPPING = "stopping"

CONTROL_STYLES = {
    CONTROL_RUNNING: ("● 推送中", MINT),
    CONTROL_PAUSED: ("Ⅱ 已暂停", WARM),
    CONTROL_RELOADING: ("↻ 正在重载", SKY),
    CONTROL_STOPPING: ("× 正在停止", ROSE),
}

COMMAND_ALIASES = {
    "p": COMMAND_PAUSE,
    "pause": COMMAND_PAUSE,
    "暂停": COMMAND_PAUSE,
    "继续": COMMAND_PAUSE,
    "r": COMMAND_RESTART,
    "reload": COMMAND_RESTART,
    "restart": COMMAND_RESTART,
    "重载": COMMAND_RESTART,
    "重启": COMMAND_RESTART,
    "x": COMMAND_STOP,
    "q": COMMAND_STOP,
    "quit": COMMAND_STOP,
    "exit": COMMAND_STOP,
    "stop": COMMAND_STOP,
    "退出": COMMAND_STOP,
    "停止": COMMAND_STOP,
    "\x03": COMMAND_STOP,
    "\x1b": COMMAND_STOP,
}


def supports_color(stream) -> bool:
    if "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
        return False
    force_color = os.environ.get("FORCE_COLOR")
    if force_color is not None:
        return force_color not in {"", "0", "false", "False"}
    return bool(getattr(stream, "isatty", lambda: False)())


def parse_command(value: str | None) -> str | None:
    if value is None:
        return None
    return COMMAND_ALIASES.get(value.strip().lower())


def supports_keyboard_control(stream=None) -> bool:
    stream = stream or sys.stdin
    if os.environ.get("PYCHARM_HOSTED") not in {None, "", "0", "false", "False"}:
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _paint(text: str, color: str, enabled: bool, *, bold: bool = False) -> str:
    if not enabled:
        return text
    weight = BOLD if bold else ""
    return f"{weight}{color}{text}{RESET}"


def _render_controls(
    *,
    color: bool,
    state: str = CONTROL_RUNNING,
) -> tuple[str, str]:
    status_text, status_color = CONTROL_STYLES.get(
        state, CONTROL_STYLES[CONTROL_RUNNING]
    )
    status = _paint(status_text, status_color, color, bold=True)
    pause_key = _paint("[p]", MINT, color, bold=True)
    restart_key = _paint("[r]", SKY, color, bold=True)
    stop_key = _paint("[x]", ROSE, color, bold=True)
    rendered = (
        f"  {status}  {pause_key} 暂停/继续  "
        f"{restart_key} 重载  {stop_key} 停止"
    )
    plain = (
        f"  {status_text}  [p] 暂停/继续  "
        f"[r] 重载  [x] 停止"
    )
    return rendered, plain


def _display_width(text: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
        for character in text
    )


class CozyFormatter(logging.Formatter):
    def __init__(self, *, color: bool):
        super().__init__()
        self._color = color

    def format(self, record: logging.LogRecord) -> str:
        symbol, color = LEVEL_STYLES.get(record.levelno, ("·", SKY))
        timestamp = self.formatTime(record, "%H:%M:%S")
        time_part = _paint(timestamp, GRAY, self._color)
        symbol_part = _paint(symbol, color, self._color, bold=True)
        message = record.getMessage()
        line = f"[{time_part}] {symbol_part}  {message}"

        if record.exc_info:
            traceback = self.formatException(record.exc_info)
            line += "\n" + indent(traceback, "           ")
        return line


class BottomCommandBar:
    def __init__(self, stream=None):
        self.stream = stream or sys.stdout
        self._color = supports_color(self.stream)
        self._lock = threading.RLock()
        self._visible = False
        self._state = CONTROL_RUNNING
        self._clear_width = 0

    def show(self, state: str = CONTROL_RUNNING) -> None:
        with self._lock:
            if self._visible:
                self._clear_locked()
            self._visible = True
            self._state = state
            self._draw_locked()

    def update(self, state: str) -> None:
        with self._lock:
            self._state = state
            if not self._visible:
                return
            self._clear_locked()
            self._draw_locked()

    def write_log(self, message: str) -> None:
        with self._lock:
            if self._visible:
                self._clear_locked()
            self.stream.write(message)
            if not message.endswith("\n"):
                self.stream.write("\n")
            if self._visible:
                self._draw_locked()
            self.stream.flush()

    def hide(self) -> None:
        with self._lock:
            if self._visible:
                self._clear_locked()
            self._visible = False
            self.stream.flush()

    def _draw_locked(self) -> None:
        terminal_width = max(
            12, shutil.get_terminal_size(fallback=(100, 24)).columns
        )
        rendered, plain = _render_controls(
            color=self._color,
            state=self._state,
        )
        if _display_width(plain) >= terminal_width:
            status_text, status_color = CONTROL_STYLES.get(
                self._state, CONTROL_STYLES[CONTROL_RUNNING]
            )
            status = _paint(status_text, status_color, self._color, bold=True)
            rendered = f" {status}  [p] [r] [x]"
            plain = f" {status_text}  [p] [r] [x]"
        self._clear_width = min(terminal_width - 1, _display_width(plain) + 2)
        self.stream.write(rendered)
        self.stream.flush()

    def _clear_locked(self) -> None:
        terminal_width = max(
            12, shutil.get_terminal_size(fallback=(100, 24)).columns
        )
        clear_width = min(terminal_width - 1, max(self._clear_width, 1))
        self.stream.write("\r" + (" " * clear_width) + "\r")


class CozyHandler(logging.Handler):
    def __init__(self, command_bar: BottomCommandBar):
        super().__init__()
        self._command_bar = command_bar

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._command_bar.write_log(self.format(record))
        except Exception:
            self.handleError(record)


def configure_logging(stream=None, level=logging.INFO) -> BottomCommandBar:
    command_bar = BottomCommandBar(stream)
    handler = CozyHandler(command_bar)
    handler.setFormatter(CozyFormatter(color=supports_color(command_bar.stream)))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    return command_bar


def print_banner(stream=None) -> None:
    stream = stream or sys.stdout
    color = supports_color(stream)
    title = _paint("ClassPad", SKY, color, bold=True)
    sparkle = _paint("✦", MINT, color, bold=True)
    stream.write("\n")
    stream.write(f"  ╭─ {sparkle} {title} · Quote/0 电子课表\n")
    stream.write("  ╰─ 正在安静守候每一节课\n\n")
    stream.flush()


def print_controls(stream=None) -> None:
    stream = stream or sys.stdout
    rendered, _ = _render_controls(color=supports_color(stream))
    stream.write(f"{rendered}\n")
    stream.flush()


class ConsoleCommandReader:
    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        key_reader: Callable[[], str | None] | None = None,
        on_command: Callable[[str], None] | None = None,
        poll_interval: float = 0.05,
    ):
        self._stream = stream or sys.stdin
        self._key_reader = key_reader
        self._on_command = on_command
        self._poll_interval = poll_interval
        self._commands: queue.Queue[str] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return True
        if self._key_reader is None and not supports_keyboard_control(self._stream):
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="classpad-console",
            daemon=True,
        )
        self._thread.start()
        return True

    def get_command(self, timeout: float | None = None) -> str | None:
        try:
            return self._commands.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(0.2, self._poll_interval * 2))

    def _run(self) -> None:
        try:
            if self._key_reader is not None:
                self._run_custom_reader()
            elif os.name == "nt":
                if self._uses_stream_reader():
                    self._run_stream_reader()
                else:
                    self._run_windows_reader()
            else:
                self._run_posix_reader()
        except (EOFError, OSError, StopIteration):
            return
        except KeyboardInterrupt:
            self._accept_key("\x03")

    def _run_custom_reader(self) -> None:
        while not self._stop_event.is_set():
            key = self._key_reader()
            if key is None:
                self._stop_event.wait(self._poll_interval)
                continue
            self._accept_key(key)

    def _run_stream_reader(self) -> None:
        while not self._stop_event.is_set():
            key = self._stream.read(1)
            if key == "":
                return
            self._accept_key(key)

    def _run_windows_reader(self) -> None:
        import msvcrt

        while not self._stop_event.is_set():
            if not msvcrt.kbhit():
                self._stop_event.wait(self._poll_interval)
                continue

            key = msvcrt.getwch()
            if key in {"\x00", "\xe0"}:
                msvcrt.getwch()
                continue
            self._accept_key(key)

    def _run_posix_reader(self) -> None:
        import select
        import termios
        import tty

        descriptor = self._stream.fileno()
        previous_settings = termios.tcgetattr(descriptor)
        tty.setcbreak(descriptor)
        cbreak_settings = termios.tcgetattr(descriptor)
        cbreak_settings[3] &= ~termios.ECHO
        termios.tcsetattr(descriptor, termios.TCSADRAIN, cbreak_settings)
        try:
            while not self._stop_event.is_set():
                readable, _, _ = select.select(
                    [self._stream], [], [], self._poll_interval
                )
                if readable:
                    self._accept_key(self._stream.read(1))
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, previous_settings)

    def _accept_key(self, key: str) -> None:
        command = parse_command(key)
        if command is None:
            return
        if self._on_command is not None:
            self._on_command(command)
        else:
            self._commands.put(command)

    def _uses_stream_reader(self) -> bool:
        """Use stdin for PyCharm's emulated/PTY terminal.

        A real Windows console is best served by ``msvcrt``.  PyCharm's
        terminal, however, is commonly backed by a pipe or ConPTY handle, so
        reading one character from stdin is the portable path there.
        """
        pycharm_hosted = os.environ.get("PYCHARM_HOSTED") not in {
            None,
            "",
            "0",
            "false",
            "False",
        }
        return pycharm_hosted
