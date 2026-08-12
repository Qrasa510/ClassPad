import logging
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from src.models import PushTarget, RuntimeConfig


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.yaml"
DEFAULT_DEVICES_FILE = "devices.yaml"
DEFAULT_CSES_FILE = "schedule/example.yaml"
DEFAULT_OWNER = "Qrasa"


class ConfigError(ValueError):
    pass


def _require_yaml() -> None:
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
        "cses_file": DEFAULT_CSES_FILE,
    }


def _ensure_yaml_file(path: Path, default_data: dict) -> None:
    _require_yaml()
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml_module: Any = yaml
    with path.open("w", encoding="utf-8") as file:
        yaml_module.safe_dump(default_data, file, allow_unicode=True, sort_keys=False)
    logger.warning("为你准备好了配置文件 · %s · 填写后重新启动即可", path)


def _load_yaml_mapping(path: Path, default_data: dict) -> dict:
    _ensure_yaml_file(path, default_data)
    yaml_module: Any = yaml
    try:
        with path.open("r", encoding="utf-8") as file:
            values = yaml_module.safe_load(file) or {}
    except yaml_module.YAMLError as exc:
        raise ConfigError(f"YAML 格式错误: {path}: {exc}") from exc
    if not isinstance(values, dict):
        raise ConfigError(f"配置文件顶层必须是对象: {path}")
    return values


def _positive_int(values: dict, name: str, default: int) -> int:
    value = values.get(name, default)
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} 必须是正整数，当前值: {value!r}") from exc
    if result < 1:
        raise ConfigError(f"{name} 必须大于 0，当前值: {result}")
    return result


def load_runtime_config(path=DEFAULT_CONFIG_FILE) -> RuntimeConfig:
    config_path = Path(path).resolve()
    values = get_default_runtime_config() | _load_yaml_mapping(
        config_path, get_default_runtime_config()
    )

    devices_value = str(values.get("devices_file") or "").strip()
    if not devices_value:
        raise ConfigError("config.yaml 缺少 devices_file")
    devices_file = Path(devices_value)
    if not devices_file.is_absolute():
        devices_file = config_path.parent / devices_file

    cses_value = str(values.get("cses_file") or "").strip()
    if not cses_value:
        raise ConfigError("config.yaml 缺少 cses_file")
    cses_file = Path(cses_value)
    if not cses_file.is_absolute():
        cses_file = PROJECT_ROOT / cses_file
    cses_file = cses_file.resolve()
    if not cses_file.is_file():
        raise ConfigError(f"CSES 文件不存在: {cses_file}")

    return RuntimeConfig(
        push_interval_seconds=_positive_int(values, "push_interval_seconds", 30),
        request_timeout_seconds=_positive_int(values, "request_timeout_seconds", 15),
        devices_file=devices_file.resolve(),
        cses_file=cses_file,
    )


def load_push_targets(path: Path) -> list[PushTarget]:
    devices_path = Path(path)
    values = _load_yaml_mapping(devices_path, get_default_devices_config())
    token_items = values.get("tokens")
    if not isinstance(token_items, list) or not token_items:
        raise ConfigError(f"设备配置必须包含非空 tokens 列表: {devices_path}")

    targets = []
    for token_index, token_item in enumerate(token_items, start=1):
        if not isinstance(token_item, dict):
            raise ConfigError(f"tokens 第 {token_index} 项必须是对象")
        token = str(token_item.get("token") or "").strip()
        if not token:
            raise ConfigError(f"tokens 第 {token_index} 项缺少 token")

        devices = token_item.get("devices")
        if not isinstance(devices, list) or not devices:
            raise ConfigError(f"tokens 第 {token_index} 项必须包含非空 devices 列表")

        default_owner = str(token_item.get("owner") or DEFAULT_OWNER)
        for device_index, device in enumerate(devices, start=1):
            if not isinstance(device, dict):
                raise ConfigError(
                    f"tokens 第 {token_index} 项的 devices 第 {device_index} 项必须是对象"
                )
            device_id = str(device.get("sn") or "").strip()
            if not device_id:
                raise ConfigError(
                    f"tokens 第 {token_index} 项的 devices 第 {device_index} 项缺少 sn"
                )
            targets.append(
                PushTarget(
                    token=token,
                    device_id=device_id,
                    owner=str(device.get("owner") or default_owner),
                    location=str(device.get("location") or "").strip(),
                )
            )
    return targets
