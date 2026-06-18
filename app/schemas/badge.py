from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BadgeBase(BaseModel):
    code: str
    name: str
    description: str
    tier: str
    icon_key: str


class EarnedBadge(BadgeBase):
    awarded_at: datetime
    extra: dict[str, Any] = {}


class LockedBadge(BadgeBase):
    progress: int
    threshold: int
    metric_label: str


class MyBadgesResponse(BaseModel):
    earned: list[EarnedBadge]
    locked: list[LockedBadge]
    newly_earned: list[BadgeBase]


class UserBadgesResponse(BaseModel):
    earned: list[EarnedBadge]


class MarkSeenResponse(BaseModel):
    success: bool
