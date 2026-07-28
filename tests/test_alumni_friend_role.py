"""Tests for the alumni_friend role introduced in FR22.

Covers three behaviours:
- Register validation: graduation_year required for role=alumni, ignored
  (nulled) for role=alumni_friend.
- Admin verify: optional `role` override on the request payload flips
  the row and clears graduation_year when needed.
- Profile update: an alumni_friend can't accidentally acquire a
  graduation_year by PUTting one.
"""
from __future__ import annotations

from fastapi import HTTPException
import pytest

from app.api.routes.admin.verify_user import verify_user as admin_verify_user_route
from app.api.routes.profile.profile import update_profile
from app.models.users import Admin, Alumni
from app.schemas.auth import AdminVerifyRequest, RegisterRequest
from app.schemas.profile import ProfileUpdateRequest


def _alumnus(**overrides) -> Alumni:
    defaults = dict(
        id="u-1",
        email="u@innopolis.university",
        hashed_password="x",
        first_name="U",
        last_name="U",
        graduation_year="2024",
        role="alumni",
        is_verified=False,
        is_banned=False,
    )
    defaults.update(overrides)
    return Alumni(**defaults)


def _admin() -> Admin:
    return Admin(id="a-1", email="admin@innopolis.university", hashed_password="x")


# ─────────────────────────── register validation ────────────────────────


class TestRegisterValidation:
    def test_alumni_requires_graduation_year(self):
        with pytest.raises(ValueError):
            RegisterRequest(
                first_name="A",
                last_name="B",
                graduation_year=None,
                email="a@innopolis.university",
                telegram_alias="tg_alias",
                password="password123",
            )

    def test_alumni_rejects_blank_graduation_year(self):
        with pytest.raises(ValueError):
            RegisterRequest(
                first_name="A",
                last_name="B",
                graduation_year="   ",
                email="a@innopolis.university",
                telegram_alias="tg_alias",
                password="password123",
            )

    def test_friend_defaults_to_null_year_even_if_supplied(self):
        req = RegisterRequest(
            first_name="A",
            last_name="B",
            role="alumni_friend",
            graduation_year="2024",  # sneaky — should be nulled
            email="a@innopolis.university",
            telegram_alias="tg_alias",
            password="password123",
        )
        assert req.graduation_year is None
        assert req.role == "alumni_friend"

    def test_bad_role_rejected(self):
        with pytest.raises(ValueError):
            RegisterRequest(
                first_name="A",
                last_name="B",
                graduation_year="2024",
                role="mystery",
                email="a@innopolis.university",
                telegram_alias="tg_alias",
                password="password123",
            )


# ─────────────────────────── admin verify override ──────────────────────


class TestAdminVerifyRoleOverride:
    @pytest.mark.asyncio
    async def test_non_admin_forbidden(self, db_session):
        alice = _alumnus()
        db_session.add(alice)
        db_session.commit()
        with pytest.raises(HTTPException) as exc:
            await admin_verify_user_route(
                request=AdminVerifyRequest(email=alice.email),
                background_tasks=_BgTasksStub(),
                db=db_session,
                current_user=alice,
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_role_override_to_friend_clears_year(self, db_session):
        alice = _alumnus(graduation_year="2024", role="alumni")
        db_session.add(alice)
        db_session.commit()
        await admin_verify_user_route(
            request=AdminVerifyRequest(email=alice.email, role="alumni_friend"),
            background_tasks=_BgTasksStub(),
            db=db_session,
            current_user=_admin(),
        )
        db_session.refresh(alice)
        assert alice.role == "alumni_friend"
        assert alice.graduation_year is None

    @pytest.mark.asyncio
    async def test_no_role_field_leaves_role_untouched(self, db_session):
        alice = _alumnus(role="alumni_friend", graduation_year=None)
        db_session.add(alice)
        db_session.commit()
        await admin_verify_user_route(
            request=AdminVerifyRequest(email=alice.email),
            background_tasks=_BgTasksStub(),
            db=db_session,
            current_user=_admin(),
        )
        db_session.refresh(alice)
        assert alice.role == "alumni_friend"


# ─────────────────────────── profile update guard ───────────────────────


class TestProfileUpdateIgnoresFriendYear:
    @pytest.mark.asyncio
    async def test_friend_cannot_set_graduation_year_via_profile_update(
        self, db_session
    ):
        friend = _alumnus(role="alumni_friend", graduation_year=None)
        db_session.add(friend)
        db_session.commit()
        await update_profile(
            profile_data=ProfileUpdateRequest(graduation_year="2024"),
            current_user=friend,
            db=db_session,
        )
        db_session.refresh(friend)
        assert friend.graduation_year is None

    @pytest.mark.asyncio
    async def test_regular_alumnus_can_update_their_year(self, db_session):
        alice = _alumnus(graduation_year="2023")
        db_session.add(alice)
        db_session.commit()
        await update_profile(
            profile_data=ProfileUpdateRequest(graduation_year="2024"),
            current_user=alice,
            db=db_session,
        )
        db_session.refresh(alice)
        assert alice.graduation_year == "2024"


class _BgTasksStub:
    """Stand-in for FastAPI's BackgroundTasks — we don't care about the
    email side-effect in these tests."""

    def add_task(self, *args, **kwargs):
        return None
