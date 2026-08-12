import io
import logging
import os
import threading
import unittest
from unittest.mock import patch

from src.console import (
    COMMAND_PAUSE,
    COMMAND_RESTART,
    COMMAND_STOP,
    CONTROL_PAUSED,
    BottomCommandBar,
    ConsoleCommandReader,
    CozyFormatter,
    parse_command,
    print_banner,
    print_controls,
    supports_color,
)


class FakeTerminal(io.StringIO):
    @staticmethod
    def isatty():
        return True


class ConsoleTests(unittest.TestCase):
    def test_plain_formatter_has_symbol_without_ansi_codes(self):
        record = logging.LogRecord("test", logging.INFO, "", 0, "一切就绪", (), None)
        output = CozyFormatter(color=False).format(record)
        self.assertIn("✦  一切就绪", output)
        self.assertNotIn("\033[", output)

    def test_colored_formatter_uses_ansi_codes(self):
        record = logging.LogRecord("test", logging.ERROR, "", 0, "出了点问题", (), None)
        output = CozyFormatter(color=True).format(record)
        self.assertIn("\033[", output)
        self.assertIn("×", output)

    def test_no_color_environment_disables_color(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            self.assertFalse(supports_color(FakeTerminal()))

    def test_banner_contains_service_identity(self):
        stream = io.StringIO()
        print_banner(stream)
        output = stream.getvalue()
        self.assertIn("ClassPad · Quote/0 电子课表", output)
        self.assertIn("正在安静守候每一节课", output)

    def test_parse_command_accepts_keys_and_aliases(self):
        self.assertEqual(COMMAND_PAUSE, parse_command("P"))
        self.assertEqual(COMMAND_RESTART, parse_command("restart"))
        self.assertEqual(COMMAND_RESTART, parse_command("重启"))
        self.assertEqual(COMMAND_STOP, parse_command("停止"))
        self.assertIsNone(parse_command("随便看看"))

    def test_controls_explain_direct_single_key_input(self):
        stream = io.StringIO()
        print_controls(stream)
        output = stream.getvalue()
        self.assertIn("[p]", output)
        self.assertIn("[r]", output)
        self.assertIn("[x]", output)
        self.assertNotIn("回车", output)

    def test_command_reader_emits_each_key_without_newline(self):
        keys = iter(["P", "r", "x"])
        reader = ConsoleCommandReader(
            key_reader=lambda: next(keys),
            poll_interval=0.001,
        )

        try:
            self.assertTrue(reader.start())
            self.assertEqual(COMMAND_PAUSE, reader.get_command(timeout=0.2))
            self.assertEqual(COMMAND_RESTART, reader.get_command(timeout=0.2))
            self.assertEqual(COMMAND_STOP, reader.get_command(timeout=0.2))
        finally:
            reader.stop()

    def test_command_callback_runs_in_reader_thread_immediately(self):
        keys = iter(["p"])
        received = []
        callback_finished = threading.Event()

        def on_command(command):
            received.append(command)
            callback_finished.set()

        reader = ConsoleCommandReader(
            key_reader=lambda: next(keys),
            on_command=on_command,
            poll_interval=0.001,
        )

        try:
            self.assertTrue(reader.start())
            self.assertTrue(callback_finished.wait(timeout=0.2))
            self.assertEqual([COMMAND_PAUSE], received)
        finally:
            reader.stop()

    def test_command_bar_is_redrawn_below_each_log(self):
        stream = io.StringIO()
        command_bar = BottomCommandBar(stream)
        command_bar.show()
        command_bar.write_log("第一条日志")
        command_bar.update(CONTROL_PAUSED)
        command_bar.write_log("第二条日志")

        output = stream.getvalue()
        self.assertLess(output.rfind("第二条日志"), output.rfind("[p]"))
        self.assertNotIn("回车", output)
        self.assertIn("已暂停", output[output.rfind("第二条日志") :])


if __name__ == "__main__":
    unittest.main()
