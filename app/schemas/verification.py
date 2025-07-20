from datetime import datetime

from pydantic import BaseModel


class EmailVerificationResponse(BaseModel):
    id: str
    alumni_id: str
    verification_code: str
    verification_code_expires: datetime
    verification_requested_at: datetime
    manual_verification_requested: bool
    verified_at: datetime | None = None

    class Config:
        from_attributes = True
