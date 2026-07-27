"""Authorization and response tests for manual badge admin endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
import pytest

from app.api.routes.admin.badges_award import AwardRequest, admin_award_badge
from app.api.routes.admin.badges_revoke import RevokeRequest, admin_revoke_badge
from app.models.users import Admin, Alumni
from app.services.badges import ManualAwardError


def _admin() -> Admin:
    return Admin(id="admin-1", email="admin@innopolis.university")


def _alumni() -> Alumni:
    return Alumni(
        id="alumni-1",
        email="alumni@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
    )


def _db_with_alumni(alumni: Alumni) -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = alumni
    return db


@pytest.mark.asyncio
async def test_award_requires_admin(db_session):
    with pytest.raises(HTTPException, match="Admin privileges") as exc:
        await admin_award_badge(
            AwardRequest(alumni_id="alumni-1", badge_code="open_source"),
            db=db_session,
            current_user=_alumni(),
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_award_returns_auditable_badge_and_notifies(mocker):
    alumni = _alumni()
    row = MagicMock(
        id="award-1",
        awarded_at=datetime(2026, 1, 1, tzinfo=UTC),
        awarded_by="admin-1",
        extra={"reason": "correction"},
    )
    award = mocker.patch(
        "app.api.routes.admin.badges_award.manual_award", return_value=row
    )
    notify = mocker.patch(
        "app.api.routes.admin.badges_award.notify_badge_awards",
        new_callable=AsyncMock,
    )

    response = await admin_award_badge(
        AwardRequest(
            alumni_id=alumni.id,
            badge_code="open_source",
            metadata={"reason": "correction"},
        ),
        db=_db_with_alumni(alumni),
        current_user=_admin(),
    )

    assert response["awarded_by"] == "admin-1"
    award.assert_called_once()
    notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_award_converts_service_errors_to_clean_400(mocker):
    alumni = _alumni()
    mocker.patch(
        "app.api.routes.admin.badges_award.manual_award",
        side_effect=ManualAwardError("Badge does not exist"),
    )

    with pytest.raises(HTTPException, match="does not exist") as exc:
        await admin_award_badge(
            AwardRequest(alumni_id=alumni.id, badge_code="unknown"),
            db=_db_with_alumni(alumni),
            current_user=_admin(),
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_revoke_requires_admin_and_returns_metadata(mocker):
    alumni = _alumni()
    mocker.patch(
        "app.api.routes.admin.badges_revoke.manual_revoke",
        return_value=MagicMock(code="local_legend"),
    )

    response = await admin_revoke_badge(
        RevokeRequest(
            alumni_id=alumni.id,
            badge_code="local_legend",
            metadata={"city": "Dubai"},
        ),
        db=_db_with_alumni(alumni),
        current_user=_admin(),
    )

    assert response == {
        "alumni_id": alumni.id,
        "badge_code": "local_legend",
        "metadata": {"city": "Dubai"},
    }
