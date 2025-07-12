from pydantic import BaseModel

class AllowedEmailResponse(BaseModel):
    success: bool
    message: str