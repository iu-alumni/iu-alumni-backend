"""Tests for the email OTP login flow.

This is a full authentication path, so the behaviours worth pinning down are the
ones that keep it from becoming a bypass: account state checks, the resend
cooldown, single-use codes, expiry, and the wrong-code attempt counter that
eventually burns the session.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.login_otp import (
    OTP_MAX_ATTEMPTS,
    login_otp_request,
    login_otp_verify,
)
from app.models.login_code import LoginCode
from app.models.users import Alumni
from app.schemas.auth import LoginOTPRequest, LoginVerifyRequest


def _alumni(
    email: str = "ada@innopolis.university",
    *,
    is_verified: bool = True,
    is_banned: bool = False,
) -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
        is_verified=is_verified,
        is_banned=is_banned,
    )


def _login_code(alumni_id: str, **overrides) -> LoginCode:
    now = datetime.now(UTC).replace(tzinfo=None)
    values = {
        "id": str(uuid.uuid4()),
        "alumni_id": alumni_id,
        "session_token": str(uuid.uuid4()),
        "code": "123456",
        "expires_at": now + timedelta(minutes=10),
        "created_at": now,
        "used": False,
        "attempts": 0,
    }
    values.update(overrides)
    return LoginCode(**values)


def _patch_email(mocker, *, sent: bool = True):
    return mocker.patch(
        "app.api.routes.authentication.login_otp.send_login_code_email",
        return_value=sent,
    )


# ── request ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_rejects_unknown_account(db_session, mocker):
    _patch_email(mocker)

    with pytest.raises(HTTPException) as exc:
        await login_otp_request(
            LoginOTPRequest(email="nobody@innopolis.university"), db=db_session
        )

    assert exc.value.status_code == 401
    assert db_session.query(LoginCode).count() == 0


@pytest.mark.asyncio
async def test_request_rejects_unverified_account(db_session, mocker):
    _patch_email(mocker)
    user = _alumni(is_verified=False)
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await login_otp_request(LoginOTPRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 401
    assert "verified" in exc.value.detail.lower()
    assert db_session.query(LoginCode).count() == 0


@pytest.mark.asyncio
async def test_request_rejects_banned_account(db_session, mocker):
    _patch_email(mocker)
    user = _alumni(is_banned=True)
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await login_otp_request(LoginOTPRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 401
    assert "banned" in exc.value.detail.lower()
    # A banned user must never get a usable login code.
    assert db_session.query(LoginCode).count() == 0


@pytest.mark.asyncio
async def test_request_issues_code_and_emails_it(db_session, mocker):
    send_email = _patch_email(mocker)
    user = _alumni()
    db_session.add(user)
    db_session.commit()

    response = await login_otp_request(LoginOTPRequest(email=user.email), db=db_session)

    code = db_session.query(LoginCode).filter_by(alumni_id=user.id).one()
    assert response.session_token == code.session_token
    assert code.used is False
    assert code.attempts == 0
    # The code goes to the account's own address, never one supplied by the caller.
    assert send_email.call_args.kwargs["email"] == user.email
    assert send_email.call_args.kwargs["code"] == code.code


@pytest.mark.asyncio
async def test_request_is_rate_limited_within_cooldown(db_session, mocker):
    _patch_email(mocker)
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    db_session.add(_login_code(user.id))
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await login_otp_request(LoginOTPRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 429
    assert db_session.query(LoginCode).count() == 1


@pytest.mark.asyncio
async def test_request_after_cooldown_invalidates_previous_code(db_session, mocker):
    _patch_email(mocker)
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    stale = _login_code(
        user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
    )
    stale_token = stale.session_token
    db_session.add(stale)
    db_session.commit()

    await login_otp_request(LoginOTPRequest(email=user.email), db=db_session)

    # Only the newest code may remain usable.
    remaining = db_session.query(LoginCode).all()
    assert len(remaining) == 1
    assert remaining[0].session_token != stale_token


@pytest.mark.asyncio
async def test_request_surfaces_email_delivery_failure(db_session, mocker):
    _patch_email(mocker, sent=False)
    user = _alumni()
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await login_otp_request(LoginOTPRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 500


# ── verify ───────────────────────────────────────────────────────────────────


def test_verify_rejects_unknown_session(db_session):
    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token="nope", code="123456"), db=db_session
        )

    assert exc.value.status_code == 401


def test_verify_rejects_used_session(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(user.id, used=True)
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 401


def test_verify_rejects_expired_code(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(
        user.id,
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
    )
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_verify_counts_wrong_attempts(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token=code.session_token, code="000000"),
            db=db_session,
        )

    assert exc.value.status_code == 401
    db_session.refresh(code)
    assert code.attempts == 1
    # The code stays usable until the attempt budget runs out.
    assert code.used is False


def test_verify_burns_session_at_max_attempts(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(user.id, attempts=OTP_MAX_ATTEMPTS)
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 429
    db_session.refresh(code)
    # Burned, so even the correct code cannot revive this session.
    assert code.used is True


def test_verify_exhausting_attempts_locks_out_correct_code(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    for _ in range(OTP_MAX_ATTEMPTS):
        with pytest.raises(HTTPException):
            login_otp_verify(
                LoginVerifyRequest(session_token=code.session_token, code="000000"),
                db=db_session,
            )

    # Brute forcing past the budget must not be rescued by finally guessing right.
    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 429


def test_verify_succeeds_and_consumes_the_code(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    response = login_otp_verify(
        LoginVerifyRequest(session_token=code.session_token, code="123456"),
        db=db_session,
    )

    assert response.access_token
    assert response.token_type == "bearer"
    db_session.refresh(code)
    assert code.used is True


def test_verify_code_cannot_be_replayed(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    login_otp_verify(
        LoginVerifyRequest(session_token=code.session_token, code="123456"),
        db=db_session,
    )

    with pytest.raises(HTTPException) as exc:
        login_otp_verify(
            LoginVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 401
