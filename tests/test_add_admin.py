"""Tests for creating admin accounts.

This is the highest-privilege operation in the app — it mints an account that can
ban users, delete alumni and create further admins — so the guard against
non-admins calling it, and the password never being stored in the clear, are the
things that matter.
"""

import uuid

from fastapi import HTTPException
import pytest

from app.api.routes.authentication.add_admin import add_admin
from app.core.security import verify_password
from app.models.users import Admin, Alumni
from app.schemas.auth import AdminCreateRequest


def _admin(email: str = "admin@innopolis.university") -> Admin:
    return Admin(id=str(uuid.uuid4()), email=email, hashed_password="hash")


def _alumni() -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email="ada@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
    )


def test_alumni_cannot_create_an_admin(db_session):
    with pytest.raises(HTTPException) as exc:
        add_admin(
            AdminCreateRequest(email="new@innopolis.university", password="Passw0rd!"),
            db=db_session,
            current_user=_alumni(),
        )

    assert exc.value.status_code == 403
    # Privilege escalation guard: nothing may be created by a rejected caller.
    assert db_session.query(Admin).count() == 0


def test_admin_can_create_another_admin(db_session):
    creator = _admin()
    db_session.add(creator)
    db_session.commit()

    result = add_admin(
        AdminCreateRequest(email="new@innopolis.university", password="Passw0rd!"),
        db=db_session,
        current_user=creator,
    )

    assert result["email"] == "new@innopolis.university"
    created = db_session.query(Admin).filter_by(email="new@innopolis.university").one()
    assert created.id


def test_created_admin_password_is_hashed(db_session):
    creator = _admin()
    db_session.add(creator)
    db_session.commit()

    add_admin(
        AdminCreateRequest(email="new@innopolis.university", password="Passw0rd!"),
        db=db_session,
        current_user=creator,
    )

    created = db_session.query(Admin).filter_by(email="new@innopolis.university").one()
    # Never stored in the clear, and the hash must actually validate.
    assert created.hashed_password != "Passw0rd!"
    assert verify_password("Passw0rd!", created.hashed_password)


def test_duplicate_admin_email_is_rejected(db_session):
    creator = _admin()
    existing = _admin("taken@innopolis.university")
    db_session.add_all([creator, existing])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        add_admin(
            AdminCreateRequest(email="taken@innopolis.university", password="Passw0rd!"),
            db=db_session,
            current_user=creator,
        )

    assert exc.value.status_code == 400
    # The existing admin's credentials must not be overwritten by a re-create.
    assert db_session.query(Admin).filter_by(email="taken@innopolis.university").count() == 1
    db_session.refresh(existing)
    assert existing.hashed_password == "hash"


def test_new_admins_get_distinct_ids(db_session):
    creator = _admin()
    db_session.add(creator)
    db_session.commit()

    add_admin(
        AdminCreateRequest(email="one@innopolis.university", password="Passw0rd!"),
        db=db_session,
        current_user=creator,
    )
    add_admin(
        AdminCreateRequest(email="two@innopolis.university", password="Passw0rd!"),
        db=db_session,
        current_user=creator,
    )

    ids = {a.id for a in db_session.query(Admin).all()}
    assert len(ids) == 3
