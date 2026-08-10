from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    push_interval_seconds: int
    request_timeout_seconds: int
    devices_file: Path
    cses_file: Path


@dataclass(frozen=True)
class PushTarget:
    token: str
    device_id: str
    owner: str
    location: str = ""

    @property
    def key(self) -> str:
        return f"{self.token}::{self.device_id}"


@dataclass(frozen=True)
class Course:
    start: str
    end: str
    name: str
    simplified_name: str
    teacher: str = ""
