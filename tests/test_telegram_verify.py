"""Tests for linking a Telegram account to an alumni account.

Confirming this link flips `is_telegram_verified`, which is exactly the flag the
Telegram OTP login path requires. A weak link here is an account-takeover route,
so single use, expiry and the pre-checks before a token is ever issued are the
behaviours under test.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.telegram_verify import (
    telegram_verify_confirm,
    telegram_verify_request,
)
from app.models.telegram import TelegramUser
from app.models.telegram_verify_token import TelegramVerifyToken
from app.models.users import Admin, Alumni


ALIAS = "ada_lovelace"


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _alumni(
    *, telegram_alias: str | None = ALIAS, is_telegram_verified: bool = False
) -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
        telegram_alias=telegram_alias,
        is_telegram_verified=is_telegram_verified,
    )


def _token(alumni_id: str, **overrides) -> TelegramVerifyToken:
    values = {
        "id": str(uuid.uuid4()),
        "alumni_id": alumni_id,
        "token": str(uuid.uuid4()),
        "expires_at": _now() + timedelta(hours=24),
        "used": False,
        "created_at": _now(),
    }
    values.update(overrides)
    return TelegramVerifyToken(**values)


def _patch_email(mocker, *, sent: bool = True):
    return mocker.patch(
        "app.api.routes.authentication.telegram_verify.send_telegram_verification_email",
        return_value=sent,
    )


# ── request ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_rejects_admin_accounts(db_session, mocker):
    _patch_email(mocker)
    admin = Admin(id=str(uuid.uuid4()), email="admin@innopolis.university")

    with pytest.raises(HTTPException) as exc:
        await telegram_verify_request(db=db_session, current_user=admin)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_request_requires_an_alias(db_session, mocker):
    send = _patch_email(mocker)
    user = _alumni(telegram_alias=None)
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await telegram_verify_request(db=db_session, current_user=user)

    assert exc.value.status_code == 400
    assert db_session.query(TelegramVerifyToken).count() == 0
    send.assert_not_called()


@pytest.mark.asyncio
async def test_request_requires_the_bot_to_be_started(db_session, mocker):
    send = _patch_email(mocker)
    user = _alumni()
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await telegram_verify_request(db=db_session, current_user=user)

    assert exc.value.status_code == 400
    assert db_session.query(TelegramVerifyToken).count() == 0
    send.assert_not_called()


@pytest.mark.asyncio
async def test_request_issues_a_token_and_emails_the_link(db_session, mocker):
    send = _patch_email(mocker)
    user = _alumni()
    db_session.add_all([user, TelegramUser(alias=ALIAS, chat_id=4242)])
    db_session.commit()

    await telegram_verify_request(db=db_session, current_user=user)

    token = db_session.query(TelegramVerifyToken).filter_by(alumni_id=user.id).one()
    assert token.used is False
    assert token.expires_at > _now()
    # The link goes to the account's email, not to Telegram — that is the point
    # of the flow: it proves control of both channels.
    assert send.call_args.kwargs["email"] == user.email
    assert token.token in send.call_args.kwargs["verify_link"]


@pytest.mark.asyncio
async def test_request_invalidates_previous_unused_tokens(db_session, mocker):
    _patch_email(mocker)
    user = _alumni()
    db_session.add_all([user, TelegramUser(alias=ALIAS, chat_id=4242)])
    db_session.commit()
    stale = _token(user.id)
    stale_value = stale.token
    db_session.add(stale)
    db_session.commit()

    await telegram_verify_request(db=db_session, current_user=user)

    remaining = db_session.query(TelegramVerifyToken).all()
    assert len(remaining) == 1
    assert remaining[0].token != stale_value


@pytest.mark.asyncio
async def test_request_surfaces_email_failure(db_session, mocker):
    _patch_email(mocker, sent=False)
    user = _alumni()
    db_session.add_all([user, TelegramUser(alias=ALIAS, chat_id=4242)])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await telegram_verify_request(db=db_session, current_user=user)

    assert exc.value.status_code == 500


# ── confirm ──────────────────────────────────────────────────────────────────


def test_confirm_verifies_the_account(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id)
    db_session.add(token)
    db_session.commit()

    response = telegram_verify_confirm(token=token.token, db=db_session)

    assert response.status_code == 200
    db_session.refresh(user)
    db_session.refresh(token)
    # This flag is what unlocks Telegram OTP login.
    assert user.is_telegram_verified is True
    assert token.used is True


def test_confirm_rejects_unknown_token(db_session):
    response = telegram_verify_confirm(token="does-not-exist", db=db_session)

    assert response.status_code == 400


def test_confirm_rejects_a_used_token(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id, used=True)
    db_session.add(token)
    db_session.commit()

    response = telegram_verify_confirm(token=token.token, db=db_session)

    assert response.status_code == 400
    db_session.refresh(user)
    assert user.is_telegram_verified is False


def test_confirm_rejects_an_expired_token(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id, expires_at=_now() - timedelta(minutes=1))
    db_session.add(token)
    db_session.commit()

    response = telegram_verify_confirm(token=token.token, db=db_session)

    assert response.status_code == 400
    db_session.refresh(user)
    assert user.is_telegram_verified is False


def test_confirm_handles_a_deleted_account(db_session):
    token = _token(str(uuid.uuid4()))
    db_session.add(token)
    db_session.commit()

    response = telegram_verify_confirm(token=token.token, db=db_session)

    # The alumnus was deleted after the link was sent.
    assert response.status_code == 404


def test_confirm_link_cannot_be_replayed(db_session):
    user = _alumni()
    db_session.add(user)
    db_session.commit()
    token = _token(user.id)
    db_session.add(token)
    db_session.commit()

    telegram_verify_confirm(token=token.token, db=db_session)
    second = telegram_verify_confirm(token=token.token, db=db_session)

    # A forwarded or leaked link must not re-verify later.
    assert second.status_code == 400
