"""Pydantic schemas for Telegram bot interactions."""

from datetime import datetime

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
    options: list[str]


class PollResponse(BaseModel):
    """Schema for poll response."""

    poll_id: str
    question: str
    options: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    alias: str | None = None
    question: str
    answer: str


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    id: int
    alias: str | None = None
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramUpdate(BaseModel):
    """Schema for an incoming Telegram update (used internally by polling)."""

    update_id: int
    message: dict | None = None
    poll_answer: dict | None = None
