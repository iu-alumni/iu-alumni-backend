"""Tests for the password reset request/confirm flow.

These endpoints guard account recovery, so the behaviours that matter are the
security ones: no email enumeration, the resend cooldown, single-use tokens,
expiry, and that a successful reset actually rotates the password hash.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.password_reset_confirm import (
    PASSWORD_RESET_MAX_ATTEMPTS,
    password_reset_confirm,
)
from app.api.routes.authentication.password_reset_request import password_reset_request
from app.core.security import verify_password
from app.models.password_reset_token import PasswordResetToken
from app.models.users import Alumni
from app.schemas.auth import PasswordResetConfirmSchema, PasswordResetRequestSchema


OPAQUE_MESSAGE = "If that email is registered, a reset link has been sent"


def _alumni(email: str = "ada@innopolis.university") -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password="old-hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
        is_verified=True,
        is_banned=False,
    )


def _token(alumni_id: str, **overrides) -> PasswordResetToken:
    now = datetime.now(UTC).replace(tzinfo=None)
    values = {
        "id": str(uuid.uuid4()),
        "alumni_id": alumni_id,
        "token": str(uuid.uuid4()),
        "expires_at": now + timedelta(minutes=30),
        "used": False,
        "created_at": now,
        "attempts": 0,
    }
    values.update(overrides)
    return PasswordResetToken(**values)


class _BackgroundTasks:
    """Minimal stand-in that records scheduled work instead of running it."""

    def __init__(self):
        self.tasks = []

    def add_task(self, func, **kwargs):
        self.tasks.append((func, kwargs))


# ── request ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_does_not_reveal_unknown_email(db_session):
    background = _BackgroundTasks()

    result = await password_reset_request(
        PasswordResetRequestSchema(email="nobody@innopolis.university"),
        background,
        db=db_session,
    )

    # Same opaque message as the success path — otherwise the endpoint becomes
    # an account-enumeration oracle.
    assert result["message"] == OPAQUE_MESSAGE
    assert background.tasks == []
    assert db_session.query(PasswordResetToken).count() == 0


@pytest.mark.asyncio
async def test_request_creates_token_and_schedules_email(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    background = _BackgroundTasks()

    result = await password_reset_request(
        PasswordResetRequestSchema(email=user.email), background, db=db_session
    )

    assert result["message"] == OPAQUE_MESSAGE
    token = db_session.query(PasswordResetToken).filter_by(alumni_id=user.id).one()
    assert token.used is False
    assert token.expires_at > datetime.now(UTC).replace(tzinfo=None)
    assert len(background.tasks) == 1
    _, kwargs = background.tasks[0]
    assert kwargs["email"] == user.email
    assert token.token in kwargs["reset_link"]


@pytest.mark.asyncio
async def test_request_is_rate_limited_within_cooldown(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    existing = _token(user.id)
    db_session.add(existing)
    db_session.commit()
    background = _BackgroundTasks()

    result = await password_reset_request(
        PasswordResetRequestSchema(email=user.email), background, db=db_session
    )

    # Rate-limited responses stay opaque, and must not issue a second token.
    assert result["message"] == OPAQUE_MESSAGE
    assert background.tasks == []
    assert db_session.query(PasswordResetToken).count() == 1


@pytest.mark.asyncio
async def test_request_after_cooldown_replaces_previous_token(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    stale = _token(
        user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
    )
    stale_value = stale.token
    db_session.add(stale)
    db_session.commit()
    background = _BackgroundTasks()

    await password_reset_request(
        PasswordResetRequestSchema(email=user.email), background, db=db_session
    )

    # The previous unused token must be invalidated so only one link works.
    remaining = db_session.query(PasswordResetToken).all()
    assert len(remaining) == 1
    assert remaining[0].token != stale_value


# ── confirm ──────────────────────────────────────────────────────────────────


def test_confirm_rejects_unknown_token(db_session):
    with pytest.raises(HTTPException) as exc:
        password_reset_confirm(
            PasswordResetConfirmSchema(token="does-not-exist", new_password="NewPassw0rd!"),
            db=db_session,
        )

    assert exc.value.status_code == 400


def test_confirm_rejects_used_token(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id, used=True)
    db_session.add(token)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        password_reset_confirm(
            PasswordResetConfirmSchema(token=token.token, new_password="NewPassw0rd!"),
            db=db_session,
        )

    assert exc.value.status_code == 400


def test_confirm_rejects_expired_token(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(
        user.id,
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
    )
    db_session.add(token)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        password_reset_confirm(
            PasswordResetConfirmSchema(token=token.token, new_password="NewPassw0rd!"),
            db=db_session,
        )

    assert exc.value.status_code == 400
    assert "expired" in exc.value.detail.lower()


def test_confirm_burns_token_at_max_attempts(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id, attempts=PASSWORD_RESET_MAX_ATTEMPTS)
    db_session.add(token)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        password_reset_confirm(
            PasswordResetConfirmSchema(token=token.token, new_password="NewPassw0rd!"),
            db=db_session,
        )

    assert exc.value.status_code == 429
    # The token is burned so a retry cannot keep hammering it.
    db_session.refresh(token)
    assert token.used is True


def test_confirm_updates_password_and_consumes_token(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id)
    db_session.add(token)
    db_session.commit()

    result = password_reset_confirm(
        PasswordResetConfirmSchema(token=token.token, new_password="NewPassw0rd!"),
        db=db_session,
    )

    assert result["message"] == "Password updated successfully"
    db_session.refresh(user)
    db_session.refresh(token)
    assert verify_password("NewPassw0rd!", user.hashed_password)
    assert token.used is True


def test_confirm_token_cannot_be_replayed(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id)
    db_session.add(token)
    db_session.commit()

    password_reset_confirm(
        PasswordResetConfirmSchema(token=token.token, new_password="FirstPassw0rd!"),
        db=db_session,
    )

    with pytest.raises(HTTPException) as exc:
        password_reset_confirm(
            PasswordResetConfirmSchema(token=token.token, new_password="SecondPassw0rd!"),
            db=db_session,
        )

    assert exc.value.status_code == 400
    db_session.refresh(user)
    assert verify_password("FirstPassw0rd!", user.hashed_password)
