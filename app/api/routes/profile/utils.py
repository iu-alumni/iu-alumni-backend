from app.models.users import Admin, Alumni
from app.schemas.profile import ProfileResponse


def build_profile_response(user: Alumni, current_user: Alumni | Admin | None = None) -> ProfileResponse:
    is_following = False
    if isinstance(current_user, Alumni) and current_user.id != user.id:
        is_following = user in current_user.following

    return ProfileResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        graduation_year=user.graduation_year,
        location=user.location,
        biography=user.biography,
        show_location=user.show_location,
        telegram_alias=user.telegram_alias,
        is_telegram_verified=user.is_telegram_verified,
        avatar=user.avatar,
        followers_count=len(user.followers) if user.followers is not None else 0,
        following_count=len(user.following) if user.following is not None else 0,
        is_following=is_following,
    )
