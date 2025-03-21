from pydantic import BaseModel, EmailStr, Field

class VerifyGraduateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    graduation_year: str
    first_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str 

class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str