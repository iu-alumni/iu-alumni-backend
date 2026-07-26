"""Tests for admin event moderation: approve / decline / unapprove.

These routes decide what alumni actually see, and each one is admin-only, so the
things worth pinning are the authorization gate, the state transitions between
pending/approved/declined, and that a non-admin can never move an event.
"""

from datetime import UTC, datetime
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.admin.approve_event import approve_event
from app.api.routes.admin.decline_event import decline_event
from app.api.routes.admin.unapprove_event import unapprove_event
from app.models.events import Event
from app.models.users import Admin, Alumni


def _admin() -> Admin:
    return Admin(id=str(uuid.uuid4()), email="admin@innopolis.university")


def _alumni() -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
    )


def _event(owner_id: str, *, approved: bool | None = None) -> Event:
    return Event(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        participants_ids=[],
        title="Alumni meetup",
        description="A meetup",
        location="Innopolis",
        datetime=datetime.now(UTC).replace(tzinfo=None),
        cost=0.0,
        is_online=False,
        cover=None,
        approved=approved,
    )


def _seed_event(db_session, *, approved: bool | None = None) -> Event:
    owner = _alumni()
    db_session.add(owner)
    db_session.commit()
    event = _event(owner.id, approved=approved)
    db_session.add(event)
    db_session.commit()
    return event


# ── authorization ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("route", [approve_event, decline_event, unapprove_event])
async def test_non_admin_cannot_moderate(db_session, route):
    event = _seed_event(db_session)

    with pytest.raises(HTTPException) as exc:
        await route(event_id=event.id, db=db_session, current_user=_alumni())

    assert exc.value.status_code == 403
    # The event must be untouched by a rejected caller.
    db_session.refresh(event)
    assert event.approved is None


@pytest.mark.asyncio
@pytest.mark.parametrize("route", [approve_event, decline_event, unapprove_event])
async def test_missing_event_is_404(db_session, route):
    with pytest.raises(HTTPException) as exc:
        await route(event_id="does-not-exist", db=db_session, current_user=_admin())

    assert exc.value.status_code == 404


# ── approve ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approve_moves_pending_event_to_approved(db_session):
    event = _seed_event(db_session, approved=None)

    result = await approve_event(event_id=event.id, db=db_session, current_user=_admin())

    assert result.approved is True
    db_session.refresh(event)
    assert event.approved is True


@pytest.mark.asyncio
async def test_approve_can_recover_a_declined_event(db_session):
    event = _seed_event(db_session, approved=False)

    await approve_event(event_id=event.id, db=db_session, current_user=_admin())

    # Declining is not terminal — an admin can still approve afterwards.
    db_session.refresh(event)
    assert event.approved is True


@pytest.mark.asyncio
async def test_approve_rejects_an_already_approved_event(db_session):
    event = _seed_event(db_session, approved=True)

    with pytest.raises(HTTPException) as exc:
        await approve_event(event_id=event.id, db=db_session, current_user=_admin())

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_commits_an_awarded_founding_host_badge(db_session, mocker):
    event = _seed_event(db_session, approved=None)
    mocker.patch("app.services.badges.evaluate_for_user", return_value=None)
    award = mocker.patch(
        "app.services.badges.award_founding_host", return_value=object()
    )

    result = await approve_event(event_id=event.id, db=db_session, current_user=_admin())

    assert result.approved is True
    # The host is evaluated for the badge as part of approving their event.
    assert award.call_args.args[1].id == event.owner_id


@pytest.mark.asyncio
async def test_approve_survives_badge_evaluation_failure(db_session, mocker):
    event = _seed_event(db_session, approved=None)
    mocker.patch(
        "app.services.badges.evaluate_for_user",
        side_effect=RuntimeError("badge backend down"),
    )

    result = await approve_event(event_id=event.id, db=db_session, current_user=_admin())

    # Badge evaluation is best-effort; a failure there must not block moderation
    # or leave the event in a half-approved state.
    assert result.approved is True
    db_session.refresh(event)
    assert event.approved is True


# ── decline ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decline_moves_pending_event_to_declined(db_session):
    event = _seed_event(db_session, approved=None)

    result = await decline_event(event_id=event.id, db=db_session, current_user=_admin())

    assert result.approved is False
    db_session.refresh(event)
    assert event.approved is False


@pytest.mark.asyncio
async def test_decline_can_revoke_an_approved_event(db_session):
    event = _seed_event(db_session, approved=True)

    await decline_event(event_id=event.id, db=db_session, current_user=_admin())

    db_session.refresh(event)
    assert event.approved is False


@pytest.mark.asyncio
async def test_decline_rejects_an_already_declined_event(db_session):
    event = _seed_event(db_session, approved=False)

    with pytest.raises(HTTPException) as exc:
        await decline_event(event_id=event.id, db=db_session, current_user=_admin())

    assert exc.value.status_code == 400


# ── unapprove ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("starting_state", [True, False, None])
async def test_unapprove_returns_event_to_pending(db_session, starting_state):
    event = _seed_event(db_session, approved=starting_state)

    result = await unapprove_event(
        event_id=event.id, db=db_session, current_user=_admin()
    )

    # Unapprove is the reset for every state, so it is idempotent from pending too.
    assert result["event"].approved is None
    db_session.refresh(event)
    assert event.approved is None
