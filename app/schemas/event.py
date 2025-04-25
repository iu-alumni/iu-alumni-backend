from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any
import dateutil.parser

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
    approved: Optional[bool] = None

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
    datetime: Optional[Any] = None
    cost: Optional[float] = None
    is_online: Optional[bool] = None
    cover: Optional[str] = None
    
    def __init__(self, **data):
        if 'datetime' in data and data['datetime'] and isinstance(data['datetime'], str):
            data['datetime'] = dateutil.parser.parse(data['datetime'])
        super().__init__(**data)