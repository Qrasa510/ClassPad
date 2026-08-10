import tempfile
import unittest
from pathlib import Path
import yaml

from src.config_store import (
    ConfigError,
    DEFAULT_CSES_FILE,
    load_push_targets,
    load_runtime_config,
)


class ConfigStoreTests(unittest.TestCase):
    def test_default_cses_path_is_cross_platform(self):
        self.assertEqual(DEFAULT_CSES_FILE, "schedule/example.yaml")

    def test_runtime_paths_are_resolved_from_documented_bases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_dir = root / "config"
            config_dir.mkdir()
            schedule = root / "schedule.yaml"
            schedule.write_text("version: 1\nsubjects: []\nschedules: []\n", encoding="utf-8")
            config_file = config_dir / "config.yaml"
            config_file.write_text(
                yaml.safe_dump(
                    {
                        "push_interval_seconds": 20,
                        "request_timeout_seconds": 8,
                        "devices_file": "devices.yaml",
                        "cses_file": str(schedule),
                    }
                ),
                encoding="utf-8",
            )

            config = load_runtime_config(config_file)

            self.assertEqual(config.devices_file, (config_dir / "devices.yaml").resolve())
            self.assertEqual(config.cses_file, schedule.resolve())

    def test_invalid_positive_integer_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schedule = root / "schedule.yaml"
            schedule.write_text("version: 1\nsubjects: []\nschedules: []\n", encoding="utf-8")
            config_file = root / "config.yaml"
            config_file.write_text(
                yaml.safe_dump(
                    {
                        "push_interval_seconds": 0,
                        "cses_file": str(schedule),
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "push_interval_seconds"):
                load_runtime_config(config_file)

    def test_missing_cses_file_is_rejected_at_load(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            config_file.write_text(
                yaml.safe_dump({"cses_file": str(Path(directory) / "missing.yaml")}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "CSES 文件不存在"):
                load_runtime_config(config_file)

    def test_empty_token_reports_its_position(self):
        with tempfile.TemporaryDirectory() as directory:
            devices_file = Path(directory) / "devices.yaml"
            devices_file.write_text(
                yaml.safe_dump({"tokens": [{"token": "", "devices": [{"sn": "abc"}]}]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "第 1 项缺少 token"):
                load_push_targets(devices_file)

    def test_valid_devices_are_converted_to_models(self):
        with tempfile.TemporaryDirectory() as directory:
            devices_file = Path(directory) / "devices.yaml"
            devices_file.write_text(
                yaml.safe_dump(
                    {
                        "tokens": [
                            {
                                "token": "secret",
                                "owner": "Default",
                                "devices": [{"sn": "abc", "location": "Hong Kong"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            targets = load_push_targets(devices_file)
            self.assertEqual(targets[0].device_id, "abc")
            self.assertEqual(targets[0].owner, "Default")


if __name__ == "__main__":
    unittest.main()
