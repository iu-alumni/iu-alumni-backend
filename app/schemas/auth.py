import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginOTPRequest(BaseModel):
    email: EmailStr


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
    # Alumni Friends (staff / dropouts / other non-graduates) skip the
    # graduation year — the role field decides which is required.
    graduation_year: str | None = None
    role: str = Field(default="alumni", pattern="^(alumni|alumni_friend)$")
    email: EmailStr
    telegram_alias: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    manual_verification: bool = False

    @model_validator(mode="after")
    def validate_grad_year_matches_role(self):
        if self.role == "alumni_friend":
            # The field is meaningless for friends — null it regardless
            # of what the client sent so the row stays consistent.
            self.graduation_year = None
        elif self.role == "alumni":
            if self.graduation_year is None or not self.graduation_year.strip():
                raise ValueError("graduation_year is required for role='alumni'")
        return self

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
        if v.startswith("@"):
            v = v[1:]
        if not re.match(r"^[a-zA-Z0-9_]{3,32}$", v):
            raise ValueError("Invalid Telegram username format")
        return v


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(..., pattern=r"^\d{6}$")


class AdminVerifyRequest(BaseModel):
    email: EmailStr
    # Optional role override applied on verification. Handy when the user
    # registered as 'alumni' by mistake and the admin sees during review
    # that they should be 'alumni_friend' (or vice versa).
    role: str | None = Field(default=None, pattern="^(alumni|alumni_friend)$")


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


# Telegram OTP login schemas
class TelegramLoginRequest(BaseModel):
    email: EmailStr


class TelegramVerifyRequest(BaseModel):
    session_token: str
    code: str = Field(..., pattern=r"^\d{6}$")


# Telegram account verification schemas (profile)
class TelegramVerifyRequestResponse(BaseModel):
    message: str
