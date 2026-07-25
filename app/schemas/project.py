from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateProjectRequest(BaseModel):
    title: str
    description: str
    cover: str | None = None
    donation_link: str | None = None
    goal_amount: int | None = None


class UpdateProjectRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    cover: str | None = None
    donation_link: str | None = None
    goal_amount: int | None = None


class DonateRequest(BaseModel):
    # Whole rubles. Positive int only; the endpoint is for logging money
    # actually given, so a zero or negative amount doesn't make sense.
    amount: int = Field(gt=0)


class Project(BaseModel):
    id: str
    owner_id: str
    contributors_ids: list[str]
    title: str
    description: str
    cover: str | None = None
    donation_link: str | None = None
    goal_amount: int | None = None
    raised_amount: int = 0
    approved: bool | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListItem(BaseModel):
    id: str
    owner_id: str
    contributors_ids: list[str]
    title: str
    description: str
    cover: str | None = None
    donation_link: str | None = None
    goal_amount: int | None = None
    raised_amount: int = 0
    approved: bool | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateProjectResponse(BaseModel):
    id: str


class CoverResponse(BaseModel):
    cover: str | None
