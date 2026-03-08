import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginInitResponse(BaseModel):
    session_token: str
    message: str


class LoginVerifyRequest(BaseModel):
    session_token: str
    code: str = Field(..., pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    graduation_year: str
    email: EmailStr
    telegram_alias: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    manual_verification: bool = False

    @field_validator("email")
    def validate_innopolis_email(cls, v):
        allowed_domains = ["@innopolis.university", "@innopolis.ru"]
        if not any(v.endswith(domain) for domain in allowed_domains):
            raise ValueError(
                "Email must be an Innopolis email (@innopolis.university or @innopolis.ru)"
            )
        return v

    @field_validator("telegram_alias")
    def validate_telegram_alias(cls, v):
        # Remove @ if present at the beginning
        if v.startswith("@"):
            v = v[1:]
        # Validate Telegram username format
        if not re.match(r"^[a-zA-Z0-9_]{3,32}$", v):
            raise ValueError("Invalid Telegram username format")
        return v


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(..., pattern=r"^\d{6}$")


class AdminVerifyRequest(BaseModel):
    email: EmailStr


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    def validate_innopolis_email(cls, v):
        allowed_domains = ["@innopolis.university", "@innopolis.ru"]
        if not any(v.endswith(domain) for domain in allowed_domains):
            raise ValueError(
                "Email must be an Innopolis email (@innopolis.university or @innopolis.ru)"
            )
        return v
