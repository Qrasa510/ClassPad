import sys
from pathlib import Path

import yaml

from src.models import Course


ALL_DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
DAY_NAME_MAP = {
    "mon": "MON", "monday": "MON", "tue": "TUE", "tuesday": "TUE",
    "wed": "WED", "wednesday": "WED", "thu": "THU", "thursday": "THU",
    "fri": "FRI", "friday": "FRI", "sat": "SAT", "saturday": "SAT",
    "sun": "SUN", "sunday": "SUN",
}


class CsesValidationError(ValueError):
    pass


def _validate_document(path: Path) -> None:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise CsesValidationError(f"CSES YAML 格式错误: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CsesValidationError(f"CSES 文件顶层必须是对象: {path}")
    missing = [name for name in ("version", "subjects", "schedules") if name not in data]
    if missing:
        raise CsesValidationError(
            f"CSES 文件缺少必要字段: {', '.join(missing)} ({path})"
        )
    if not isinstance(data["subjects"], list):
        raise CsesValidationError(f"CSES subjects 必须是列表: {path}")
    if not isinstance(data["schedules"], list):
        raise CsesValidationError(f"CSES schedules 必须是列表: {path}")


def _normalize_time(value) -> str:
    # PyYAML follows YAML 1.1 and may parse an unquoted value such as
    # 10:00:00 as the sexagesimal integer 36000 (seconds since midnight).
    if isinstance(value, int) and not isinstance(value, bool):
        if not 0 <= value < 24 * 60 * 60:
            return ""
        hour, remainder = divmod(value, 60 * 60)
        minute, _second = divmod(remainder, 60)
        return f"{hour:02d}:{minute:02d}"

    parts = str(value or "").strip().split(":")
    if len(parts) not in {2, 3} or not all(part.isdigit() for part in parts):
        return ""

    hour, minute = int(parts[0]), int(parts[1])
    second = int(parts[2]) if len(parts) == 3 else 0
    if not 0 <= hour < 24 or not 0 <= minute < 60 or not 0 <= second < 60:
        return ""
    return f"{hour:02d}:{minute:02d}"


def _day_key(value) -> str | None:
    if isinstance(value, str):
        return DAY_NAME_MAP.get(value.lower())
    if isinstance(value, int) and 1 <= value <= 7:
        return ALL_DAYS[value - 1]
    return None


def _load_cses_module():
    bundled_path = Path(__file__).resolve().parent.parent / "lib" / "pycses"
    if bundled_path.is_dir() and str(bundled_path) not in sys.path:
        sys.path.insert(0, str(bundled_path))
    try:
        import cses
    except ImportError as exc:
        raise RuntimeError("未找到 pycses 解析器") from exc
    return cses


def _build_parser(path: Path, cses_module):
    try:
        return cses_module.CSESParser(file_path=str(path))
    except ValueError as exc:
        if "missing required field 'weeks'" not in str(exc):
            raise

    with path.open("r", encoding="utf-8") as file:
        raw_data = yaml.safe_load(file) or {}

    normalized = {"version": 1, "subjects": raw_data.get("subjects", []), "schedules": []}
    for schedule in raw_data.get("schedules", []):
        enable_day = schedule.get("enable_day")
        day_values = enable_day if isinstance(enable_day, list) else [enable_day]
        classes = schedule.get("classes", [])
        for value in day_values:
            day = _day_key(value)
            if day:
                normalized["schedules"].append(
                    {
                        "name": schedule.get("name", ""),
                        "enable_day": day.lower(),
                        "weeks": "all",
                        "classes": classes,
                    }
                )

    content = yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False)
    return cses_module.CSESParser(content=content)


def _parse_schedule(path: Path) -> dict[str, list[Course]]:
    _validate_document(path)
    parser = _build_parser(path, _load_cses_module())
    schedule = {day: [] for day in ALL_DAYS}
    subjects = {}

    for subject in parser.get_subjects():
        name = str(subject.get("name") or "").strip()
        if name:
            subjects[name] = {
                "simplified_name": str(subject.get("simplified_name") or name).strip() or name,
                "teacher": str(subject.get("teacher") or "").strip(),
            }

    for item in parser.get_schedules():
        enable_day = item.get("enable_day")
        day_values = enable_day if isinstance(enable_day, list) else [enable_day]
        days = [day for value in day_values if (day := _day_key(value))]
        if not days:
            continue

        courses = []
        for class_item in item.get("classes", []):
            name = str(class_item.get("subject") or "").strip()
            start = _normalize_time(class_item.get("start_time"))
            end = _normalize_time(class_item.get("end_time"))
            if not name or not start or not end:
                continue
            subject = subjects.get(name, {})
            courses.append(
                Course(
                    start=start,
                    end=end,
                    name=name,
                    simplified_name=subject.get("simplified_name", name),
                    teacher=subject.get("teacher", ""),
                )
            )

        for day in days:
            schedule[day].extend(courses)
            schedule[day].sort(key=lambda course: course.start)

    return schedule


class CsesScheduleProvider:
    def __init__(self, path: Path):
        self._path = Path(path)
        self._mtime = None
        self._schedule = None

    def courses_for(self, day: str) -> list[Course]:
        if not self._path.exists():
            raise FileNotFoundError(f"CSES 文件不存在: {self._path}")

        mtime = self._path.stat().st_mtime
        if self._schedule is None or self._mtime != mtime:
            self._schedule = _parse_schedule(self._path)
            self._mtime = mtime
        return self._schedule.get(day, [])

    def validate(self) -> None:
        """Parse the complete file once so configuration errors fail at startup."""
        self.courses_for(ALL_DAYS[0])
