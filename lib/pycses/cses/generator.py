import yaml
from typing import List, Optional, Union
from .types import Subject, Schedule, ClassInfo, CSESData

# Define a custom string class for times that should always be quoted
class QuotedTime(str):
    pass

# Register a representer to force quotes for QuotedTime
def quoted_time_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")

yaml.add_representer(QuotedTime, quoted_time_representer)

class CSESGenerator:
    def __init__(self, version: int = 1):
        """
        初始化 CSES 生成器 
        
        Args:
            version (int, optional): CSES 格式的版本号，默认为 1 
        """
        self.version: int = version
        self.subjects: List[Subject] = []
        self.schedules: List[Schedule] = []

    def add_subject(self, name: str, simplified_name: Optional[str] = None, 
                   teacher: Optional[str] = None, room: Optional[str] = None) -> None:
        """
        添加科目信息 
        
        Args:
            name (str): 科目名称 
            simplified_name (str, optional): 科目简称 
            teacher (str, optional): 教师姓名 
            room (str, optional): 教室名称 
        """
        subject: Subject = {
            'name': name,
            'simplified_name': simplified_name,
            'teacher': teacher,
            'room': room
        }
        self.subjects.append(subject)
    
    def _normalize_time(self, time_str: Union[str, int]) -> QuotedTime:
        """
        规范化时间格式为 HH:MM:SS，并确保输出时带有引号
        
        Args:
            time_str: 输入的时间字符串 (如 "8:00", "08:00", "08:00:00")
            
        Returns:
            QuotedTime: 格式化后的时间字符串，包装在 QuotedTime 中以强制引号
        
        Raises:
            ValueError: 如果时间格式无效
        """
        if not isinstance(time_str, str):
            time_str = str(time_str)
            
        parts = time_str.split(':')
        normalized = ""
        
        if len(parts) == 2:
            # HH:MM -> HH:MM:SS
            if not (parts[0].isdigit() and parts[1].isdigit()):
                 raise ValueError(f"Invalid time format: {time_str}")
            normalized = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
        elif len(parts) == 3:
            # HH:MM:SS -> HH:MM:SS
            if not (parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit()):
                 raise ValueError(f"Invalid time format: {time_str}")
            normalized = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
        else:
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM or HH:MM:SS")
            
        return QuotedTime(normalized)

    def add_schedule(self, name: str, enable_day: str, weeks: str, classes: List[ClassInfo]) -> None:
        """
        添加课程安排 
        
        Args:
            name (str): 课程安排名称（如 "星期一"）
            enable_day (str): 课程安排的星期（如 'mon', 'tue' 等）
            weeks (str): 周次类型（如 'all', 'odd', 'even'）
            classes (list): 课程列表，每个课程包含以下键：
                - subject (str): 科目名称 
                - start_time (str): 开始时间（如 '8:00'）
                - end_time (str): 结束时间（如 '9:00'）
        """
        if not isinstance(weeks, str):
             raise ValueError(f"Weeks must be a string, got {type(weeks)}")

        # Normalize time in classes
        normalized_classes: List[ClassInfo] = []
        for cls in classes:
            # We need to copy and cast to allow modification, 
            # though strictly TypedDict doesn't support easy dynamic modification if we want to stay 100% pure
            new_cls = cls.copy()
            if 'start_time' in new_cls:
                new_cls['start_time'] = self._normalize_time(new_cls['start_time'])
            if 'end_time' in new_cls:
                new_cls['end_time'] = self._normalize_time(new_cls['end_time'])
            normalized_classes.append(new_cls)

        schedule: Schedule = {
            'name': name,
            'enable_day': enable_day,
            'weeks': weeks,
            'classes': normalized_classes
        }
        self.schedules.append(schedule)
    
    def generate_cses_data(self) -> CSESData:
        """
        生成 CSES 格式的字典数据 
        
        Returns:
            dict: CSES 格式的字典数据 
        """
        cses_data: CSESData = {
            'version': self.version,
            'subjects': self.subjects,
            'schedules': self.schedules
        }
        return cses_data

    def to_string(self) -> str:
        """
        将 CSES 数据转换为 YAML 字符串
        
        Returns:
            str: YAML 格式的字符串
        """
        cses_data = self.generate_cses_data()
        return yaml.dump(cses_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def save_to_file(self, file_path: str) -> None:
        """
        将 CSES 数据保存到 YAML 文件 
        
        Args:
            file_path (str): 输出文件路径 
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_string())
        except IOError as e:
            raise IOError(f"Failed to write {file_path}: {e}")
