"""Tests for the /projects surface.

Covers CRUD, admin approval, and the contribute flow. Uses direct-call
style (same convention as `test_event_participants.py`) rather than
`client` HTTP fixtures — keeps tests fast and free of auth plumbing.

Approval is tri-state: None = pending, True = approved, False = declined.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from pydantic import ValidationError
import pytest

from app.api.routes.admin.list_all_projects import admin_list_projects
from app.api.routes.admin.projects_approve import (
    approve_project,
    decline_project,
    unapprove_project,
)
from app.api.routes.projects.contribute import contribute, retract_contribution
from app.api.routes.projects.create_project import create_project
from app.api.routes.projects.delete_project import delete_project
from app.api.routes.projects.donate import donate
from app.api.routes.projects.get_project import get_project
from app.api.routes.projects.list_contributed_projects import (
    list_my_contributed_projects,
    list_user_contributed_projects,
)
from app.api.routes.projects.list_owner_projects import list_owner_projects
from app.api.routes.projects.list_projects import list_projects
from app.api.routes.projects.update_project import update_project
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import (
    CreateProjectRequest,
    DonateRequest,
    UpdateProjectRequest,
)


def _alumni(user_id: str) -> Alumni:
    return Alumni(
        id=user_id,
        email=f"{user_id}@innopolis.university",
        hashed_password="x",
        first_name="First",
        last_name="Last",
        graduation_year="2025",
    )


def _admin() -> Admin:
    return Admin(
        id="admin-" + uuid.uuid4().hex[:6],
        email="admin@innopolis.university",
        hashed_password="x",
    )


def _seed_project(
    db,
    *,
    owner_id: str,
    approved: bool | None = None,
    title: str = "Alumni Lounge",
    description: str = "Furnishing the new on-campus alumni lounge.",
    contributors: list[str] | None = None,
    donation_link: str = "https://tinkoff.ru/rm/example",
    goal_amount: int = 100000,
) -> Project:
    project = Project(
        id="p-" + uuid.uuid4().hex[:8],
        owner_id=owner_id,
        contributors_ids=list(contributors or []),
        title=title,
        description=description,
        cover=None,
        approved=approved,
        donation_link=donation_link,
        goal_amount=goal_amount,
        raised_amount=0,
    )
    db.add(project)
    db.commit()
    return project


# ─────────────────────────── CRUD ──────────────────────────────────────


class TestCreateProject:
    @pytest.mark.asyncio
    async def test_creates_as_pending(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        res = await create_project(
            body=CreateProjectRequest(
                title="Campus Greenhouse",
                description="Year-round greenhouse.",
                donation_link="https://tinkoff.ru/rm/greenhouse",
                goal_amount=500000,
            ),
            db=db_session,
            current_user=alice,
        )

        stored = db_session.query(Project).filter(Project.id == res.id).one()
        assert stored.owner_id == alice.id
        assert stored.approved is None
        assert stored.contributors_ids == []

    @pytest.mark.parametrize(
        "donation_link",
        [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "ftp://example.com/donate",
            "not-a-url",
        ],
    )
    def test_rejects_non_http_donation_links(self, donation_link):
        with pytest.raises(ValidationError, match="donation_link"):
            CreateProjectRequest(
                title="Campus Greenhouse",
                description="Year-round greenhouse.",
                donation_link=donation_link,
                goal_amount=500000,
            )

    @pytest.mark.asyncio
    async def test_admin_cannot_create(self, db_session):
        with pytest.raises(HTTPException) as exc:
            await create_project(
                body=CreateProjectRequest(title="T", description="D"),
                db=db_session,
                current_user=_admin(),
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_blank_title_rejected(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        with pytest.raises(HTTPException) as exc:
            await create_project(
                body=CreateProjectRequest(title="   ", description="D"),
                db=db_session,
                current_user=alice,
            )
        assert exc.value.status_code == 422


class TestListPublic:
    @pytest.mark.asyncio
    async def test_only_approved_projects_visible(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        _seed_project(db_session, owner_id=alice.id, approved=True, title="Public")
        _seed_project(db_session, owner_id=alice.id, approved=None, title="Draft")
        _seed_project(db_session, owner_id=alice.id, approved=False, title="Declined")

        bob = _alumni("bob")
        db_session.add(bob)
        db_session.commit()

        page = await list_projects(
            search=None,
            cursor=None,
            limit=50,
            db=db_session,
            current_user=bob,
        )
        titles = [p.title for p in page.items]
        assert titles == ["Public"]

    @pytest.mark.asyncio
    async def test_search_filters_by_title(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        _seed_project(db_session, owner_id=alice.id, approved=True, title="Greenhouse")
        _seed_project(db_session, owner_id=alice.id, approved=True, title="Lounge")

        page = await list_projects(
            search="green",
            cursor=None,
            limit=50,
            db=db_session,
            current_user=alice,
        )
        assert [p.title for p in page.items] == ["Greenhouse"]


class TestGetOne:
    @pytest.mark.asyncio
    async def test_pending_hidden_from_others(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        pending = _seed_project(db_session, owner_id=alice.id, approved=None)

        with pytest.raises(HTTPException) as exc:
            await get_project(
                project_id=pending.id, db=db_session, current_user=bob
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_pending_visible_to_owner_and_admin(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        pending = _seed_project(db_session, owner_id=alice.id, approved=None)

        by_owner = await get_project(
            project_id=pending.id, db=db_session, current_user=alice
        )
        assert by_owner.id == pending.id
        by_admin = await get_project(
            project_id=pending.id, db=db_session, current_user=_admin()
        )
        assert by_admin.id == pending.id


class TestUpdate:
    @pytest.mark.asyncio
    async def test_non_owner_forbidden(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        with pytest.raises(HTTPException) as exc:
            await update_project(
                project_id=p.id,
                body=UpdateProjectRequest(title="Hack"),
                db=db_session,
                current_user=bob,
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_editing_approved_resets_to_pending(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        result = await update_project(
            project_id=p.id,
            body=UpdateProjectRequest(description="A whole new pitch"),
            db=db_session,
            current_user=alice,
        )
        assert result.approved is None

    @pytest.mark.asyncio
    async def test_no_content_change_keeps_approval(self, db_session):
        """PUT with only cover=None (unchanged) shouldn't reset approval."""
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        result = await update_project(
            project_id=p.id,
            body=UpdateProjectRequest(),
            db=db_session,
            current_user=alice,
        )
        assert result.approved is True


class TestDelete:
    @pytest.mark.asyncio
    async def test_owner_can_delete(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        await delete_project(
            project_id=p.id, db=db_session, current_user=alice
        )
        assert db_session.query(Project).filter(Project.id == p.id).first() is None

    @pytest.mark.asyncio
    async def test_admin_can_delete(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        await delete_project(
            project_id=p.id, db=db_session, current_user=_admin()
        )
        assert db_session.query(Project).filter(Project.id == p.id).first() is None

    @pytest.mark.asyncio
    async def test_stranger_forbidden(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        with pytest.raises(HTTPException) as exc:
            await delete_project(
                project_id=p.id, db=db_session, current_user=bob
            )
        assert exc.value.status_code == 403


# ─────────────────────────── Contribute ────────────────────────────────


class TestContribute:
    @pytest.mark.asyncio
    async def test_contribute_and_retract(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=True)

        await contribute(project_id=p.id, db=db_session, current_user=bob)
        db_session.refresh(p)
        assert bob.id in p.contributors_ids

        await retract_contribution(
            project_id=p.id, db=db_session, current_user=bob
        )
        db_session.refresh(p)
        assert bob.id not in p.contributors_ids

    @pytest.mark.asyncio
    async def test_contribute_twice_rejected(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        p = _seed_project(
            db_session,
            owner_id=alice.id,
            approved=True,
            contributors=[bob.id],
        )
        with pytest.raises(HTTPException) as exc:
            await contribute(
                project_id=p.id, db=db_session, current_user=bob
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_contribute_to_pending_forbidden(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=None)
        with pytest.raises(HTTPException) as exc:
            await contribute(
                project_id=p.id, db=db_session, current_user=bob
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_cannot_contribute(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        with pytest.raises(HTTPException) as exc:
            await contribute(
                project_id=p.id, db=db_session, current_user=_admin()
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_retract_when_not_contributor_400(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()
        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        with pytest.raises(HTTPException) as exc:
            await retract_contribution(
                project_id=p.id, db=db_session, current_user=bob
            )
        assert exc.value.status_code == 400


class TestDonate:
    @pytest.mark.asyncio
    async def test_donation_increments_total_and_adds_contributor(
        self, db_session
    ):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()
        project = _seed_project(
            db_session,
            owner_id=alice.id,
            approved=True,
        )

        result = await donate(
            project_id=project.id,
            body=DonateRequest(amount=500),
            db=db_session,
            current_user=bob,
        )

        assert result.raised_amount == 500
        assert result.contributors_ids == [bob.id]

    @pytest.mark.asyncio
    async def test_repeat_donation_accumulates_without_duplicate_contributor(
        self, db_session
    ):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()
        project = _seed_project(
            db_session,
            owner_id=alice.id,
            approved=True,
            contributors=[bob.id],
        )

        await donate(
            project_id=project.id,
            body=DonateRequest(amount=500),
            db=db_session,
            current_user=bob,
        )
        result = await donate(
            project_id=project.id,
            body=DonateRequest(amount=750),
            db=db_session,
            current_user=bob,
        )

        assert result.raised_amount == 1250
        assert result.contributors_ids == [bob.id]

    @pytest.mark.asyncio
    async def test_pending_project_rejected(self, db_session):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()
        project = _seed_project(
            db_session,
            owner_id=alice.id,
            approved=None,
        )

        with pytest.raises(HTTPException) as exc:
            await donate(
                project_id=project.id,
                body=DonateRequest(amount=500),
                db=db_session,
                current_user=bob,
            )

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_rejected(self, db_session):
        with pytest.raises(HTTPException) as exc:
            await donate(
                project_id="any-project",
                body=DonateRequest(amount=500),
                db=db_session,
                current_user=_admin(),
            )

        assert exc.value.status_code == 403


class TestContributedListers:
    # `ARRAY.any()` is a Postgres-specific comparator. The SQLite test
    # fixture rewrites ARRAY to JSON so the table can be created, but
    # `.any()` isn't wired for the JSON type. We assert the semantics
    # against the real DB in the integration environment; skipping here
    # avoids a false failure that would only be exposed by the fixture.
    @pytest.mark.skip(reason="ARRAY.any() unsupported on SQLite fixture")
    @pytest.mark.asyncio
    async def test_my_contributed_shows_only_contributed_approved(
        self, db_session
    ):
        alice, bob = _alumni("alice"), _alumni("bob")
        db_session.add_all([alice, bob])
        db_session.commit()

        contributed_approved = _seed_project(
            db_session,
            owner_id=alice.id,
            approved=True,
            title="Contributed",
            contributors=[bob.id],
        )
        _seed_project(
            db_session, owner_id=alice.id, approved=True, title="Not contributed"
        )
        # Approved -> declined shouldn't leak, even though bob contributed
        # before the decline.
        _seed_project(
            db_session,
            owner_id=alice.id,
            approved=False,
            title="Declined-old",
            contributors=[bob.id],
        )

        rows = await list_my_contributed_projects(
            skip=0, limit=50, db=db_session, current_user=bob
        )
        assert [p.title for p in rows] == [contributed_approved.title]

    @pytest.mark.asyncio
    async def test_public_view_404s_on_unknown_user(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        with pytest.raises(HTTPException) as exc:
            await list_user_contributed_projects(
                alumni_id="ghost",
                skip=0,
                limit=50,
                db=db_session,
                current_user=alice,
            )
        assert exc.value.status_code == 404


class TestOwnerLister:
    @pytest.mark.asyncio
    async def test_owner_sees_all_statuses(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        _seed_project(db_session, owner_id=alice.id, approved=True, title="A")
        _seed_project(db_session, owner_id=alice.id, approved=None, title="B")
        _seed_project(db_session, owner_id=alice.id, approved=False, title="C")

        rows = await list_owner_projects(
            skip=0, limit=50, db=db_session, current_user=alice
        )
        assert sorted(p.title for p in rows) == ["A", "B", "C"]


# ─────────────────────────── Admin ─────────────────────────────────────


class TestAdminApproval:
    @pytest.mark.asyncio
    async def test_approve_pending(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()

        p = _seed_project(db_session, owner_id=alice.id, approved=None)
        result = await approve_project(
            project_id=p.id, db=db_session, current_user=_admin()
        )
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_reapprove_400(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        p = _seed_project(db_session, owner_id=alice.id, approved=True)
        with pytest.raises(HTTPException) as exc:
            await approve_project(
                project_id=p.id, db=db_session, current_user=_admin()
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_decline_then_unapprove(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        p = _seed_project(db_session, owner_id=alice.id, approved=None)

        declined = await decline_project(
            project_id=p.id, db=db_session, current_user=_admin()
        )
        assert declined.approved is False

        back_to_pending = await unapprove_project(
            project_id=p.id, db=db_session, current_user=_admin()
        )
        assert back_to_pending.approved is None

    @pytest.mark.asyncio
    async def test_non_admin_forbidden(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        p = _seed_project(db_session, owner_id=alice.id, approved=None)
        with pytest.raises(HTTPException) as exc:
            await approve_project(
                project_id=p.id, db=db_session, current_user=alice
            )
        assert exc.value.status_code == 403


class TestAdminListAll:
    @pytest.mark.asyncio
    async def test_status_filter_pending(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        _seed_project(db_session, owner_id=alice.id, approved=True, title="A")
        _seed_project(db_session, owner_id=alice.id, approved=None, title="B")
        _seed_project(db_session, owner_id=alice.id, approved=False, title="C")

        page = await admin_list_projects(
            status_filter="pending",
            search=None,
            cursor=None,
            limit=50,
            db=db_session,
            current_user=_admin(),
        )
        assert [p.title for p in page.items] == ["B"]

    @pytest.mark.asyncio
    async def test_status_all_returns_everything(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        _seed_project(db_session, owner_id=alice.id, approved=True, title="A")
        _seed_project(db_session, owner_id=alice.id, approved=None, title="B")
        _seed_project(db_session, owner_id=alice.id, approved=False, title="C")

        page = await admin_list_projects(
            status_filter="all",
            search=None,
            cursor=None,
            limit=50,
            db=db_session,
            current_user=_admin(),
        )
        assert sorted(p.title for p in page.items) == ["A", "B", "C"]

    @pytest.mark.asyncio
    async def test_invalid_status_422(self, db_session):
        with pytest.raises(HTTPException) as exc:
            await admin_list_projects(
                status_filter="anything",
                search=None,
                cursor=None,
                limit=50,
                db=db_session,
                current_user=_admin(),
            )
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_non_admin_forbidden(self, db_session):
        alice = _alumni("alice")
        db_session.add(alice)
        db_session.commit()
        with pytest.raises(HTTPException) as exc:
            await admin_list_projects(
                status_filter="all",
                search=None,
                cursor=None,
                limit=50,
                db=db_session,
                current_user=alice,
            )
        assert exc.value.status_code == 403
