from typing import TypedDict, List, Optional, Union

class Subject(TypedDict):
    name: str
    simplified_name: Optional[str]
    teacher: Optional[str]
    room: Optional[str]

class ClassInfo(TypedDict):
    subject: str
    start_time: str
    end_time: str

class Schedule(TypedDict):
    name: str
    enable_day: str
    weeks: str
    classes: List[ClassInfo]

class CSESData(TypedDict):
    version: Union[int, str]
    subjects: List[Subject]
    schedules: List[Schedule]
