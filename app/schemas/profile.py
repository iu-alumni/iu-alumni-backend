from typing import Optional
from pydantic import BaseModel
from app.models.enums import GraduationCourse

class ProfileResponse(BaseModel):
    first_name: str
    last_name: str
    graduation_year: int
    course: GraduationCourse
    location: Optional[str] = None
    biography: Optional[str] = None
    show_location: bool = False
    
    class Config:
        from_attributes = True

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    course: Optional[GraduationCourse] = None
    location: Optional[str] = None
    biography: Optional[str] = None
    show_location: Optional[bool] = None 