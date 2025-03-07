from typing import Optional
from pydantic import BaseModel

class ProfileResponse(BaseModel):
    first_name: str
    last_name: str
    graduation_year: str
    location: Optional[str] = None
    biography: Optional[str] = None
    show_location: bool = False
    
    class Config:
        from_attributes = True

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    graduation_year: Optional[str] = None
    location: Optional[str] = None
    biography: Optional[str] = None
    show_location: Optional[bool] = None 