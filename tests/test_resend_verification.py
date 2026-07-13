from unittest.mock import MagicMock

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.resend_verification import resend_verification_link
from app.models.users import Alumni
from app.schemas.auth import ResendVerificationRequest


def _http_request(base_url: str = "https://api.example.test/"):
    request = MagicMock()
    request.base_url = base_url
    return request


def _alumni() -> Alumni:
    return Alumni(
        id="user-1",
        email="user@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
        is_verified=False,
        is_banned=False,
    )


@pytest.mark.asyncio
async def test_resend_verification_uses_absolute_link(db_session, mocker):
    user = _alumni()
    db_session.add(user)
    db_session.commit()

    mocker.patch(
        "app.services.verification_service.secrets.token_urlsafe",
        return_value="test-token",
    )
    send_email = mocker.patch(
        "app.api.routes.authentication.resend_verification.send_verification_link_email",
        return_value=True,
    )

    result = await resend_verification_link(
        ResendVerificationRequest(email=user.email),
        _http_request(),
        db_session,
    )

    assert result == {
        "message": "A new verification link has been sent to your email",
        "email": user.email,
    }
    send_email.assert_awaited_once_with(
        user.email,
        user.first_name,
        "https://api.example.test/api/v1/auth/verify?token=test-token",
    )


@pytest.mark.asyncio
async def test_resend_verification_reports_email_send_failure(db_session, mocker):
    user = _alumni()
    db_session.add(user)
    db_session.commit()

    mocker.patch(
        "app.api.routes.authentication.resend_verification.send_verification_link_email",
        return_value=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        await resend_verification_link(
            ResendVerificationRequest(email=user.email),
            _http_request(),
            db_session,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to send verification email. Please try again later."
