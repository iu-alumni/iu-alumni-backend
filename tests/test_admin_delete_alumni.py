"""Tests for permanently deleting an alumnus.

This is the most destructive admin route: it removes the account plus every row
referencing it across six tables, and strips the id out of other people's
events/projects. The risk is asymmetric — deleting too little leaves dangling
references, deleting too much destroys another member's content — so both
directions are asserted.
"""

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.admin.delete_alumni import delete_alumni
from app.models.email_verification import EmailVerification
from app.models.events import Event
from app.models.login_code import LoginCode
from app.models.password_reset_token import PasswordResetToken
from app.models.projects import Project
from app.models.telegram_verify_token import TelegramVerifyToken
from app.models.users import Admin, Alumni


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


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


def _event(owner_id: str, participants: list[str] | None = None) -> Event:
    return Event(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        participants_ids=participants or [],
        title="Meetup",
        description="A meetup",
        location="Innopolis",
        datetime=_now(),
        cost=0.0,
        is_online=False,
        cover=None,
        approved=True,
    )


def _project(owner_id: str, contributors: list[str] | None = None) -> Project:
    return Project(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        contributors_ids=contributors or [],
        title="Project",
        description="A project",
        cover=None,
        approved=True,
    )


def _auth_rows(db_session, alumni_id: str) -> None:
    """Seed one row in each auth-flow table that references the alumnus."""
    db_session.add(
        EmailVerification(
            id=str(uuid.uuid4()),
            alumni_id=alumni_id,
            verification_requested_at=_now(),
        )
    )
    db_session.add(
        LoginCode(
            id=str(uuid.uuid4()),
            alumni_id=alumni_id,
            session_token=str(uuid.uuid4()),
            code="123456",
            expires_at=_now() + timedelta(minutes=10),
            created_at=_now(),
            used=False,
            attempts=0,
        )
    )
    db_session.add(
        PasswordResetToken(
            id=str(uuid.uuid4()),
            alumni_id=alumni_id,
            token=str(uuid.uuid4()),
            expires_at=_now() + timedelta(minutes=30),
            used=False,
            created_at=_now(),
            attempts=0,
        )
    )
    db_session.add(
        TelegramVerifyToken(
            id=str(uuid.uuid4()),
            alumni_id=alumni_id,
            token=str(uuid.uuid4()),
            expires_at=_now() + timedelta(minutes=30),
            used=False,
            created_at=_now(),
        )
    )
    db_session.commit()


# ── authorization ────────────────────────────────────────────────────────────


def test_non_admin_cannot_delete(db_session):
    victim = _alumni()
    db_session.add(victim)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        delete_alumni(alumni_id=victim.id, db=db_session, current_user=_alumni())

    assert exc.value.status_code == 403
    # The account must still be there after a rejected call.
    assert db_session.query(Alumni).filter_by(id=victim.id).first() is not None


def test_missing_user_is_404(db_session):
    with pytest.raises(HTTPException) as exc:
        delete_alumni(alumni_id="does-not-exist", db=db_session, current_user=_admin())

    assert exc.value.status_code == 404


# ── deletion ─────────────────────────────────────────────────────────────────


def test_delete_removes_the_account(db_session):
    victim = _alumni()
    db_session.add(victim)
    db_session.commit()

    result = delete_alumni(alumni_id=victim.id, db=db_session, current_user=_admin())

    assert result["message"] == "User deleted successfully"
    assert db_session.query(Alumni).filter_by(id=victim.id).first() is None


def test_delete_removes_owned_content(db_session):
    victim = _alumni()
    db_session.add(victim)
    db_session.commit()
    db_session.add(_event(victim.id))
    db_session.add(_project(victim.id))
    db_session.commit()

    delete_alumni(alumni_id=victim.id, db=db_session, current_user=_admin())

    assert db_session.query(Event).filter_by(owner_id=victim.id).count() == 0
    assert db_session.query(Project).filter_by(owner_id=victim.id).count() == 0


def test_delete_removes_auth_flow_rows(db_session):
    victim = _alumni()
    db_session.add(victim)
    db_session.commit()
    _auth_rows(db_session, victim.id)

    delete_alumni(alumni_id=victim.id, db=db_session, current_user=_admin())

    # None of these tables cascade at the DB level, so leftovers would be
    # dangling rows pointing at an account that no longer exists.
    assert db_session.query(EmailVerification).filter_by(alumni_id=victim.id).count() == 0
    assert db_session.query(LoginCode).filter_by(alumni_id=victim.id).count() == 0
    assert db_session.query(PasswordResetToken).filter_by(alumni_id=victim.id).count() == 0
    assert db_session.query(TelegramVerifyToken).filter_by(alumni_id=victim.id).count() == 0


def test_delete_strips_id_from_other_peoples_events(db_session):
    victim = _alumni()
    other = _alumni()
    db_session.add_all([victim, other])
    db_session.commit()
    event = _event(other.id, participants=[victim.id, other.id])
    db_session.add(event)
    db_session.commit()

    delete_alumni(alumni_id=victim.id, db=db_session, current_user=_admin())

    db_session.refresh(event)
    # The other member's event survives, minus the deleted participant.
    assert db_session.query(Event).filter_by(id=event.id).first() is not None
    assert event.participants_ids == [other.id]


def test_delete_strips_id_from_other_peoples_projects(db_session):
    victim = _alumni()
    other = _alumni()
    db_session.add_all([victim, other])
    db_session.commit()
    project = _project(other.id, contributors=[victim.id, other.id])
    db_session.add(project)
    db_session.commit()

    delete_alumni(alumni_id=victim.id, db=db_session, current_user=_admin())

    db_session.refresh(project)
    assert db_session.query(Project).filter_by(id=project.id).first() is not None
    assert project.contributors_ids == [other.id]


def test_delete_leaves_unrelated_members_untouched(db_session):
    victim = _alumni()
    bystander = _alumni()
    db_session.add_all([victim, bystander])
    db_session.commit()
    their_event = _event(bystander.id, participants=[bystander.id])
    their_project = _project(bystander.id, contributors=[bystander.id])
    db_session.add_all([their_event, their_project])
    db_session.commit()
    _auth_rows(db_session, bystander.id)

    delete_alumni(alumni_id=victim.id, db=db_session, current_user=_admin())

    # Deleting one account must not touch anyone else's account, content or
    # auth-flow rows.
    assert db_session.query(Alumni).filter_by(id=bystander.id).first() is not None
    assert db_session.query(Event).filter_by(id=their_event.id).first() is not None
    assert db_session.query(Project).filter_by(id=their_project.id).first() is not None
    db_session.refresh(their_event)
    assert their_event.participants_ids == [bystander.id]
    assert db_session.query(LoginCode).filter_by(alumni_id=bystander.id).count() == 1
    assert db_session.query(PasswordResetToken).filter_by(alumni_id=bystander.id).count() == 1
