from datetime import datetime

from pydantic import BaseModel


class NotificationItem(BaseModel):
    id: str
    event_id: str
    title: str
    location: str
    datetime: datetime
    read: bool


class UnreadCountResponse(BaseModel):
    count: int
