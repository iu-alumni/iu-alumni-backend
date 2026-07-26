"""Tests for the Telegram OTP login flow.

This is a second, independent way into an account, so it needs the same
guarantees as the email OTP path plus the two gates unique to it: the account
must have a *verified* Telegram alias, and that alias must map to a real bot
chat before any code is issued.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.login_telegram_otp import (
    OTP_MAX_ATTEMPTS,
    login_telegram_request,
    login_telegram_verify,
)
from app.models.login_code import LoginCode
from app.models.telegram import TelegramUser
from app.models.users import Alumni
from app.schemas.auth import TelegramLoginRequest, TelegramVerifyRequest


ALIAS = "ada_lovelace"


def _alumni(
    email: str = "ada@innopolis.university",
    *,
    is_verified: bool = True,
    is_banned: bool = False,
    is_telegram_verified: bool = True,
    telegram_alias: str | None = ALIAS,
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
        is_telegram_verified=is_telegram_verified,
        telegram_alias=telegram_alias,
    )


def _telegram_user(alias: str = ALIAS, chat_id: int = 424242) -> TelegramUser:
    return TelegramUser(alias=alias, chat_id=chat_id)


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


def _patch_bot(mocker, *, sent: bool = True):
    return mocker.patch(
        "app.api.routes.authentication.login_telegram_otp.telegram_service.send_login_code",
        return_value=sent,
    )


def _seed(db_session, user: Alumni, *, with_bot_chat: bool = True) -> Alumni:
    db_session.add(user)
    if with_bot_chat and user.telegram_alias:
        db_session.add(_telegram_user(user.telegram_alias))
    db_session.commit()
    return user


# ── request ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_rejects_unknown_account(db_session, mocker):
    _patch_bot(mocker)

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(
            TelegramLoginRequest(email="nobody@innopolis.university"), db=db_session
        )

    assert exc.value.status_code == 401
    assert db_session.query(LoginCode).count() == 0


@pytest.mark.asyncio
async def test_request_rejects_unverified_account(db_session, mocker):
    _patch_bot(mocker)
    user = _seed(db_session, _alumni(is_verified=False))

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 401
    assert db_session.query(LoginCode).count() == 0


@pytest.mark.asyncio
async def test_request_rejects_banned_account(db_session, mocker):
    _patch_bot(mocker)
    user = _seed(db_session, _alumni(is_banned=True))

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 401
    assert "banned" in exc.value.detail.lower()
    assert db_session.query(LoginCode).count() == 0


@pytest.mark.asyncio
async def test_request_requires_verified_telegram(db_session, mocker):
    send = _patch_bot(mocker)
    user = _seed(db_session, _alumni(is_telegram_verified=False))

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    # Without this gate, claiming someone's alias would be enough to log in as them.
    assert exc.value.status_code == 403
    assert db_session.query(LoginCode).count() == 0
    send.assert_not_called()


@pytest.mark.asyncio
async def test_request_requires_a_started_bot_chat(db_session, mocker):
    send = _patch_bot(mocker)
    user = _seed(db_session, _alumni(), with_bot_chat=False)

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 400
    assert db_session.query(LoginCode).count() == 0
    send.assert_not_called()


@pytest.mark.asyncio
async def test_request_sends_code_to_the_linked_chat(db_session, mocker):
    send = _patch_bot(mocker)
    user = _seed(db_session, _alumni())

    response = await login_telegram_request(
        TelegramLoginRequest(email=user.email), db=db_session
    )

    code = db_session.query(LoginCode).filter_by(alumni_id=user.id).one()
    assert response.session_token == code.session_token
    assert code.used is False
    # The code must go to the chat bound to the account's verified alias.
    assert send.call_args.kwargs["chat_id"] == 424242
    assert send.call_args.kwargs["code"] == code.code


@pytest.mark.asyncio
async def test_request_is_rate_limited_within_cooldown(db_session, mocker):
    _patch_bot(mocker)
    user = _seed(db_session, _alumni())
    db_session.add(_login_code(user.id))
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 429
    assert db_session.query(LoginCode).count() == 1


@pytest.mark.asyncio
async def test_request_after_cooldown_invalidates_previous_code(db_session, mocker):
    _patch_bot(mocker)
    user = _seed(db_session, _alumni())
    stale = _login_code(
        user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
    )
    stale_token = stale.session_token
    db_session.add(stale)
    db_session.commit()

    await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    remaining = db_session.query(LoginCode).all()
    assert len(remaining) == 1
    assert remaining[0].session_token != stale_token


@pytest.mark.asyncio
async def test_request_surfaces_bot_delivery_failure(db_session, mocker):
    _patch_bot(mocker, sent=False)
    user = _seed(db_session, _alumni())

    with pytest.raises(HTTPException) as exc:
        await login_telegram_request(TelegramLoginRequest(email=user.email), db=db_session)

    assert exc.value.status_code == 500


# ── verify ───────────────────────────────────────────────────────────────────


def test_verify_rejects_unknown_session(db_session):
    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token="nope", code="123456"), db=db_session
        )

    assert exc.value.status_code == 401


def test_verify_rejects_used_session(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(user.id, used=True)
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 401


def test_verify_rejects_expired_code(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(
        user.id,
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
    )
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_verify_counts_wrong_attempts(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token=code.session_token, code="000000"),
            db=db_session,
        )

    assert exc.value.status_code == 401
    db_session.refresh(code)
    assert code.attempts == 1
    assert code.used is False


def test_verify_burns_session_at_max_attempts(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(user.id, attempts=OTP_MAX_ATTEMPTS)
    db_session.add(code)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 429
    db_session.refresh(code)
    assert code.used is True


def test_verify_exhausting_attempts_locks_out_correct_code(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    for _ in range(OTP_MAX_ATTEMPTS):
        with pytest.raises(HTTPException):
            login_telegram_verify(
                TelegramVerifyRequest(session_token=code.session_token, code="000000"),
                db=db_session,
            )

    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 429


def test_verify_succeeds_and_consumes_the_code(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    response = login_telegram_verify(
        TelegramVerifyRequest(session_token=code.session_token, code="123456"),
        db=db_session,
    )

    assert response.access_token
    assert response.token_type == "bearer"
    db_session.refresh(code)
    assert code.used is True


def test_verify_code_cannot_be_replayed(db_session):
    user = _seed(db_session, _alumni())
    code = _login_code(user.id, code="123456")
    db_session.add(code)
    db_session.commit()

    login_telegram_verify(
        TelegramVerifyRequest(session_token=code.session_token, code="123456"),
        db=db_session,
    )

    with pytest.raises(HTTPException) as exc:
        login_telegram_verify(
            TelegramVerifyRequest(session_token=code.session_token, code="123456"),
            db=db_session,
        )

    assert exc.value.status_code == 401
