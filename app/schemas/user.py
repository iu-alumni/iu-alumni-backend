from pydantic import BaseModel
from pydantic import ConfigDict

class Alumni(BaseModel):
    id: str
    email: str
    hashed_password: str | None = None
    first_name: str
    last_name: str
    graduation_year: str
    location: str | None = None
    biography: str | None = None
    show_location: bool
    is_verified: bool
    is_banned: bool

    model_config = ConfigDict(from_attributes=True)