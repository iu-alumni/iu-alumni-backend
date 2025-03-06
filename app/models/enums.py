from enum import Enum

class GraduationCourse(str, Enum):
    BS_CS = "Bachelor of Science in Computer Science"
    MS_CS = "Master of Science in Computer Science"
    BS_DS = "Bachelor of Science in Data Science"
    MS_DS = "Master of Science in Data Science"
    BS_RO = "Bachelor of Science in Robotics"
    PHD = "PhD"
    NONE = "None"