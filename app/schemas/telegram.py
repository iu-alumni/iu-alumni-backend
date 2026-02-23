"""Pydantic schemas for Telegram bot interactions."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class TelegramUserCreate(BaseModel):
    """Schema for creating/registering a Telegram user."""

    alias: str
    chat_id: int


class TelegramUserResponse(BaseModel):
    """Schema for Telegram user response."""

    alias: str
    chat_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PollCreate(BaseModel):
    """Schema for creating a poll."""

    poll_id: str
    question: str
    options: List[str]


class PollResponse(BaseModel):
    """Schema for poll response."""

    poll_id: str
    question: str
    options: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    alias: Optional[str] = None
    question: str
    answer: str


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    id: int
    alias: Optional[str] = None
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramUpdate(BaseModel):
    """Schema for incoming Telegram webhook update.
    
    This is a simplified version of Telegram Update object.
    Only contains the fields we care about.
    """

    update_id: int
    message: Optional[dict] = None
    poll_answer: Optional[dict] = None


class NotifyJoinRequest(BaseModel):
    """Schema for event join notification request."""

    event_name: str
    owner_alias: str
    user_alias: str


class NotifyUpcomingRequest(BaseModel):
    """Schema for upcoming event notification request."""

    event_name: str
    user_alias: str


class NotifyUserRequest(BaseModel):
    """Schema for custom user notification request."""

    event_name: str
    user_alias: str
    text: str


class NotifyAdminsRequest(BaseModel):
    """Schema for admin notification request."""

    text: str
