from pydantic import BaseModel


class AvatarResponse(BaseModel):
    avatar: str | None = None


class ProfileResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    graduation_year: str
    location: str | None = None
    biography: str | None = None
    show_location: bool = False
    telegram_alias: str | None = None
    avatar: str | None = None

    class Config:
        from_attributes = True


class ProfileListItem(BaseModel):
    """Slim profile schema for list responses — no avatar image."""

    id: str
    first_name: str
    last_name: str
    graduation_year: str
    location: str | None = None
    biography: str | None = None
    show_location: bool = False
    telegram_alias: str | None = None

    class Config:
        from_attributes = True


class MapLocationGroup(BaseModel):
    """A location pin on the alumni map: one entry per unique city."""

    country: str
    city: str
    lat: float
    lng: float
    count: int


class MapLocationsResponse(BaseModel):
    locations: list[MapLocationGroup]


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    graduation_year: str | None = None
    location: str | None = None
    biography: str | None = None
    show_location: bool | None = None
    telegram_alias: str | None = None
    avatar: str | None = None
