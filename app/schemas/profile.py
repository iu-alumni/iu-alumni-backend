from pydantic import BaseModel


class AvatarResponse(BaseModel):
    avatar: str | None = None


class FollowStatusResponse(BaseModel):
    user_id: str
    is_following: bool

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    # None for Alumni Friends (staff / dropouts / other non-graduate
    # community members). Clients render an "Alumni Friend" chip in
    # place of the graduation-year tag when role == 'alumni_friend'.
    graduation_year: str | None = None
    role: str = "alumni"
    location: str | None = None
    biography: str | None = None
    show_location: bool = False
    telegram_alias: str | None = None
    is_telegram_verified: bool = False
    avatar: str | None = None
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False

    class Config:
        from_attributes = True


class ProfileListItem(BaseModel):
    """Slim profile schema for list responses — no avatar image."""

    id: str
    first_name: str
    last_name: str
    graduation_year: str | None = None
    role: str = "alumni"
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
