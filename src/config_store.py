from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from src.models import PushTarget, RuntimeConfig


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.yaml"
DEFAULT_DEVICES_FILE = "devices.yaml"
DEFAULT_OWNER = "Qrasa"


def _require_yaml():
    if yaml is None:
        raise RuntimeError("缺少依赖 PyYAML，请先执行: pip install -r requirements.txt")


def get_default_devices_config() -> dict:
    return {
        "tokens": [
            {
                "name": "default",
                "token": "",
                "owner": DEFAULT_OWNER,
                "devices": [{"sn": ""}],
            }
        ]
    }


def get_default_runtime_config() -> dict:
    return {
        "push_interval_seconds": 30,
        "request_timeout_seconds": 15,
        "devices_file": DEFAULT_DEVICES_FILE,
        "cses_file": "schedule\\example.yaml",
    }


def _ensure_yaml_file(path: Path, default_data: dict) -> None:
    _require_yaml()
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml_module: Any = yaml
    with path.open("w", encoding="utf-8") as file:
        yaml_module.safe_dump(default_data, file, allow_unicode=True, sort_keys=False)
    print(f"已自动生成配置文件: {path}")


def _positive_int(value, default: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def load_runtime_config(path=DEFAULT_CONFIG_FILE) -> RuntimeConfig:
    config_path = Path(path).resolve()
    _ensure_yaml_file(config_path, get_default_runtime_config())
    yaml_module: Any = yaml
    with config_path.open("r", encoding="utf-8") as file:
        values = get_default_runtime_config() | (yaml_module.safe_load(file) or {})

    devices_file = Path(str(values.get("devices_file") or DEFAULT_DEVICES_FILE))
    if not devices_file.is_absolute():
        devices_file = config_path.parent / devices_file

    cses_file = Path(str(values.get("cses_file") or "schedule\\example.yaml"))
    if not cses_file.is_absolute():
        cses_file = PROJECT_ROOT / cses_file

    return RuntimeConfig(
        push_interval_seconds=_positive_int(values.get("push_interval_seconds"), 30),
        request_timeout_seconds=_positive_int(values.get("request_timeout_seconds"), 15),
        devices_file=devices_file.resolve(),
        cses_file=cses_file.resolve(),
    )


def load_push_targets(path: Path) -> list[PushTarget]:
    devices_path = Path(path)
    _ensure_yaml_file(devices_path, get_default_devices_config())
    yaml_module: Any = yaml
    with devices_path.open("r", encoding="utf-8") as file:
        values = yaml_module.safe_load(file) or {}

    targets = []
    for token_item in values.get("tokens", []):
        token = str(token_item.get("token") or "").strip()
        if not token:
            continue
        default_owner = str(token_item.get("owner") or DEFAULT_OWNER)
        for device in token_item.get("devices", []):
            device_id = str(device.get("sn") or "").strip()
            if device_id:
                targets.append(
                    PushTarget(
                        token=token,
                        device_id=device_id,
                        owner=str(device.get("owner") or default_owner),
                        location=str(device.get("location") or "").strip(),
                    )
                )
    return targets
