import yaml
from typing import List, Dict, Any, Optional, Union
from .types import Subject, Schedule, ClassInfo

class CSESParser:
    def __init__(self, file_path: Optional[str] = None, content: Optional[str] = None):
        """
        初始化 CSES 解析器
        
        Args:
            file_path (str, optional): CSES 格式的 YAML 文件路径
            content (str, optional): CSES 格式的 YAML 字符串内容
        """
        self.file_path: Optional[str] = file_path
        self.content: Optional[str] = content
        self.data: Optional[Dict[str, Any]] = None
        self.version: Optional[Union[int, str]] = None
        self.subjects: List[Subject] = []
        self.schedules: List[Schedule] = []
        
        self._load_data()
        self._parse_data()
    
    def _load_data(self) -> None:
        """加载并解析 YAML 数据（从文件或字符串）"""
        if self.content:
            try:
                self.data = yaml.safe_load(self.content)
            except yaml.YAMLError as e:
                raise ValueError(f"YAML Error: {e}")
        elif self.file_path:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = yaml.safe_load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"File {self.file_path} Not Found")
            except yaml.YAMLError as e:
                raise ValueError(f"YAML Error: {e}")
        else:
             raise ValueError("Either file_path or content must be provided")

    def _parse_data(self) -> None:
        """解析 YAML 数据"""
        if not self.data:
            return
        
        # 获取版本信息
        self.version = self.data.get('version', 1)
        
        # 解析科目信息
        subjects_data = self.data.get('subjects', [])
        if not isinstance(subjects_data, list):
             raise ValueError("Field 'subjects' must be a list")

        for i, subject in enumerate(subjects_data):
            if not isinstance(subject, dict):
                raise ValueError(f"Subject at index {i} must be a dictionary")
            
            if 'name' not in subject:
                raise ValueError(f"Subject at index {i} missing required field 'name'")

            subject_info: Subject = {
                'name': subject['name'],
                'simplified_name': subject.get('simplified_name'),
                'teacher': subject.get('teacher'),
                'room': subject.get('room')
            }
            self.subjects.append(subject_info)
        
        # 解析课程安排
        schedules_data = self.data.get('schedules', [])
        if not isinstance(schedules_data, list):
             raise ValueError("Field 'schedules' must be a list")

        for i, schedule in enumerate(schedules_data):
            if not isinstance(schedule, dict):
                raise ValueError(f"Schedule at index {i} must be a dictionary")

            required_fields = ['name', 'enable_day', 'weeks']
            for field in required_fields:
                if field not in schedule:
                    raise ValueError(f"Schedule at index {i} missing required field '{field}'")

            schedule_info: Schedule = {
                'name': schedule['name'],
                'enable_day': schedule['enable_day'],
                'weeks': schedule['weeks'],
                'classes': []
            }
            
            # 解析课程
            classes_data = schedule.get('classes', [])
            if not isinstance(classes_data, list):
                 raise ValueError(f"Field 'classes' in schedule {i} must be a list")

            for j, cls in enumerate(classes_data):
                if not isinstance(cls, dict):
                    raise ValueError(f"Class at index {j} in schedule {i} must be a dictionary")

                class_required_fields = ['subject', 'start_time', 'end_time']
                for field in class_required_fields:
                    if field not in cls:
                        raise ValueError(f"Class at index {j} in schedule {i} missing required field '{field}'")

                class_info: ClassInfo = {
                    'subject': cls['subject'],
                    'start_time': cls['start_time'],
                    'end_time': cls['end_time']
                }
                schedule_info['classes'].append(class_info)
            
            self.schedules.append(schedule_info)
    
    def get_subjects(self) -> List[Subject]:
        """获取所有科目信息"""
        return self.subjects
    
    def get_schedules(self) -> List[Schedule]:
        """获取所有课程安排"""
        return self.schedules
    
    def get_schedule_by_day(self, day: str) -> List[ClassInfo]:
        """
        根据星期获取课程安排
        
        Args:
            day (str): 星期（如 'mon', 'tue' 等）
            
        Returns:
            list: 该星期的课程安排
        """
        for schedule in self.schedules:
            if schedule['enable_day'] == day:
                return schedule['classes']
        return []
    
    @staticmethod
    def is_cses_file(file_path: str) -> bool:
        """
        判断是否为 CSES 格式的文件
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否为 CSES 文件
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return 'version' in data and 'subjects' in data and 'schedules' in data
        except Exception:
            return False
