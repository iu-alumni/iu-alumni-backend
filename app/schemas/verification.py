from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmailVerificationResponse(BaseModel):
    id: str
    alumni_id: str
    verification_code: str
    verification_code_expires: datetime
    verification_requested_at: datetime
    manual_verification_requested: bool
    verified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True