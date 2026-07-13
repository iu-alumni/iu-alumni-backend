from datetime import datetime
from typing import Any

import dateutil.parser
from pydantic import BaseModel, Field, field_validator


class CoverResponse(BaseModel):
    cover: str | None = None


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


class EventListItem(BaseModel):
    """Slim event schema for list responses — includes cover image."""

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


class AdminEventListItem(EventListItem):
    """Admin event list item — includes cover for thumbnail display."""

    cover: str | None = None


class CreateEventRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    datetime: datetime
    cost: float
    is_online: bool
    cover: str | None = None

    @field_validator("title", "description", "location", mode="before")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Field must be text")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @field_validator("cover", mode="before")
    @classmethod
    def normalize_cover(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


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

    @field_validator("title", "description", "location", mode="before")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Field must be text")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @field_validator("cover", mode="before")
    @classmethod
    def normalize_cover(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value

    def __init__(self, **data):
        if (
            "datetime" in data
            and data["datetime"]
            and isinstance(data["datetime"], str)
        ):
            data["datetime"] = dateutil.parser.parse(data["datetime"])
        super().__init__(**data)
