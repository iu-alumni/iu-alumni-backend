from datetime import datetime
from typing import Any

import dateutil.parser
from pydantic import BaseModel


class Event(BaseModel):
    id: str
    owner_id: str
    participants_ids: list[str]
    title: str
    description: str
    location: str
    datetime: datetime
    cost: float
    is_online: bool
    cover: str | None = None
    approved: bool | None = None


class CreateEventRequest(BaseModel):
    title: str
    description: str
    location: str
    datetime: datetime
    cost: float
    is_online: bool
    cover: str | None = None


class CreateEventResponse(BaseModel):
    id: str


class UpdateEventRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    datetime: Any | None = None
    cost: float | None = None
    is_online: bool | None = None
    cover: str | None = None

    def __init__(self, **data):
        if (
            "datetime" in data
            and data["datetime"]
            and isinstance(data["datetime"], str)
        ):
            data["datetime"] = dateutil.parser.parse(data["datetime"])
        super().__init__(**data)
