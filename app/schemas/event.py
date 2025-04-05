from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Event(BaseModel):
    id: str
    owner_id: str
    participants_ids: List[str]
    title: str
    description: str
    location: str
    datetime: datetime
    cost: float
    is_online: bool
    cover: Optional[str] = None

class CreateEventRequest(BaseModel):
    title: str
    description: str
    location: str
    datetime: datetime
    cost: float
    is_online: bool
    cover: Optional[str] = None

class CreateEventResponse(BaseModel):
    id: str 

class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    datetime: Optional[datetime] = None
    cost: Optional[float] = None
    is_online: Optional[bool] = None
    cover: Optional[str] = None