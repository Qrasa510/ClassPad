import unittest
from unittest.mock import Mock

from main import RuntimeControl
from src.console import (
    COMMAND_PAUSE,
    COMMAND_RESTART,
    COMMAND_STOP,
    CONTROL_PAUSED,
    CONTROL_RELOADING,
    CONTROL_RUNNING,
    CONTROL_STOPPING,
)


class RuntimeControlTests(unittest.TestCase):
    def setUp(self):
        self.command_bar = Mock()
        self.control = RuntimeControl(self.command_bar)

    def test_pause_state_changes_before_main_loop_handles_it(self):
        with self.assertLogs("main", level="INFO"):
            self.control.handle(COMMAND_PAUSE)

        self.assertTrue(self.control.paused)
        self.assertFalse(self.control.can_push())
        self.command_bar.update.assert_called_with(CONTROL_PAUSED)

    def test_restart_resumes_and_blocks_old_push_cycle(self):
        with self.assertLogs("main", level="INFO"):
            self.control.handle(COMMAND_PAUSE)
            self.control.handle(COMMAND_RESTART)

        self.assertFalse(self.control.paused)
        self.assertFalse(self.control.can_push())
        self.assertTrue(self.control.consume_restart())
        self.control.mark_reloading()
        self.assertTrue(self.control.can_push())
        self.command_bar.update.assert_called_with(CONTROL_RELOADING)
        self.assertIn(
            (CONTROL_RELOADING,),
            [item.args for item in self.command_bar.update.call_args_list],
        )

    def test_stop_updates_state_immediately(self):
        with self.assertLogs("main", level="INFO"):
            self.control.handle(COMMAND_STOP)

        self.assertTrue(self.control.stop_requested)
        self.assertFalse(self.control.can_push())
        self.command_bar.update.assert_called_with(CONTROL_STOPPING)


if __name__ == "__main__":
    unittest.main()
