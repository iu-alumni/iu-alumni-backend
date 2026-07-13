from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateProjectRequest(BaseModel):
    title: str
    description: str
    cover: str | None = None


class UpdateProjectRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    cover: str | None = None


class Project(BaseModel):
    id: str
    owner_id: str
    contributors_ids: list[str]
    title: str
    description: str
    cover: str | None = None
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
    approved: bool | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateProjectResponse(BaseModel):
    id: str


class CoverResponse(BaseModel):
    cover: str | None
