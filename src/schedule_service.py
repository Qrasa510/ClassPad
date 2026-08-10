from datetime import datetime

from src.models import Course


def _parse_time(value: str, now: datetime) -> datetime:
    hour, minute = map(int, value.split(":"))
    return datetime(now.year, now.month, now.day, hour, minute)


def _progress(start: datetime, end: datetime, now: datetime) -> int:
    total = (end - start).total_seconds()
    if total <= 0:
        return 0
    return int(max(0, min(100, (now - start).total_seconds() * 100 / total)))


def _occurrences(now: datetime, courses: list[Course]):
    result = []
    for index, course in enumerate(courses):
        result.append(
            {
                "index": index,
                "start": _parse_time(course.start, now),
                "end": _parse_time(course.end, now),
                "name": course.name,
                "simplified_name": course.simplified_name or course.name,
                "teacher": course.teacher,
            }
        )
    return result


class ScheduleService:
    def __init__(self, provider, clock=None):
        self._provider = provider
        self._clock = clock or datetime.now

    def build_canvas_data(self, owner: str, weather: str | None, now: datetime | None = None) -> dict:
        now = now or self._clock()
        day = now.strftime("%a").upper()
        courses = _occurrences(now, self._provider.courses_for(day))
        current = next((item for item in courses if item["start"] <= now < item["end"]), None)
        future = [item for item in courses if item["start"] > now]
        finished = [item for item in courses if item["end"] <= now]
        last_finished = finished[-1] if finished else None

        if current:
            period = f"正在上课 第{current['index'] + 1}节"
            course = current["name"]
            teacher = current["teacher"]
            course_time = f"{current['start']:%H:%M} — {current['end']:%H:%M}"
            remaining = max(0, int((current["end"] - now).total_seconds() // 60))
            progress = _progress(current["start"], current["end"], now)
        elif future and last_finished:
            next_course = future[0]
            period = f"下一节课程 · {next_course['name']}"
            course = "课间休息"
            teacher = next_course["teacher"]
            course_time = f"{last_finished['end']:%H:%M} — {next_course['start']:%H:%M}"
            remaining = max(0, int((next_course["start"] - now).total_seconds() // 60))
            progress = _progress(last_finished["end"], next_course["start"], now)
        elif future:
            next_course = future[0]
            period = "下一节课程"
            course = next_course["name"]
            teacher = next_course["teacher"]
            course_time = f"{next_course['start']:%H:%M} — {next_course['end']:%H:%M}"
            remaining = 0
            progress = 0
        else:
            period, course, teacher, course_time, remaining, progress = (
                "今日课程已结束", "—", "", "—", 0, 0
            )

        visible = future[:10]
        hidden = max(0, len(future) - len(visible))
        data = {
            "day": day,
            "date": f"{now.month}月{now.day}日",
            "time": now.strftime("%I:%M %p").lstrip("0"),
            "period": period,
            "course": course,
            "courseTime": course_time,
            "remaining": str(remaining),
            "progress": str(progress),
            "todayRemaining": str(len(future)),
            "teacher": f"教师 {teacher}" if teacher else "",
            "nextSeries": " ".join(item["simplified_name"] for item in visible) or "—",
            "hidden": str(hidden),
            "hiddenDisplay": "flex" if hidden else "none",
            "owner": owner,
        }
        if weather:
            data["weather"] = weather
        return data
