from pydantic import BaseModel


class EventSettingsResponse(BaseModel):
    auto_approve: bool
