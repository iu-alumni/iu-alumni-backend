from fastapi import HTTPException
import pytest

from app.api.routes.profile.get_profiles import get_profiles
from app.api.routes.profile.profile import update_profile
from app.models.users import Alumni
from app.schemas.profile import ProfileUpdateRequest


def _alumni(
    user_id: str,
    *,
    location: str | None = "Russia, Saint Petersburg",
    show_location: bool = True,
    is_verified: bool = True,
    is_banned: bool = False,
) -> Alumni:
    return Alumni(
        id=user_id,
        email=f"{user_id}@innopolis.university",
        first_name="First",
        last_name="Last",
        graduation_year="2024",
        location=location,
        biography=None,
        show_location=show_location,
        telegram_alias=None,
        avatar="avatar-data",
        is_verified=is_verified,
        is_banned=is_banned,
    )


@pytest.mark.asyncio
async def test_update_profile_rejects_blank_required_names(db_session):
    user = _alumni("user-1")
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await update_profile(
            ProfileUpdateRequest(first_name="   "),
            current_user=user,
            db=db_session,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "First name is required"


@pytest.mark.asyncio
async def test_update_profile_trims_names_and_clears_avatar(db_session):
    user = _alumni("user-1")
    db_session.add(user)
    db_session.commit()

    updated = await update_profile(
        ProfileUpdateRequest(first_name="  Ada  ", last_name="  Lovelace  ", avatar=""),
        current_user=user,
        db=db_session,
    )

    assert updated.first_name == "Ada"
    assert updated.last_name == "Lovelace"
    assert updated.avatar is None


def test_get_profiles_location_filter_matches_map_visibility_rules(db_session):
    visible = _alumni("visible")
    hidden = _alumni("hidden", show_location=False)
    unverified = _alumni("unverified", is_verified=False)
    banned = _alumni("banned", is_banned=True)
    other_city = _alumni("other-city", location="Russia, Innopolis")
    db_session.add_all([visible, hidden, unverified, banned, other_city])
    db_session.commit()

    page = get_profiles(
        search=None,
        location="russia, saint petersburg",
        cursor=None,
        limit=50,
        db=db_session,
        current_user=visible,
    )

    assert [profile.id for profile in page.items] == ["visible"]
