from fastapi import HTTPException
import pytest

from app.api.routes.admin.unban import unban_user
from app.models.users import Admin, Alumni


def test_unban_user_not_admin(db_session):
    current_user = Alumni(
        id="user123",
        email="user@example.com",
        first_name="Test",
        last_name="User",
        graduation_year="2025"
    )
    with pytest.raises(HTTPException) as exc_info:
        unban_user(user_id="any_id", db=db_session, current_user=current_user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You are not authorized to unban users"


def test_unban_user_not_found(db_session):
    admin = Admin(id="admin123", email="admin@example.com")
    db_session.add(admin)
    db_session.commit()
    with pytest.raises(HTTPException) as exc_info:
        unban_user(user_id="nonexistent_id", db=db_session, current_user=admin)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_unban_user_not_banned(db_session):
    admin = Admin(id="admin123", email="admin@example.com")
    db_session.add(admin)
    user = Alumni(
        id="user123",
        email="user@example.com",
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_banned=False
    )
    db_session.add(user)
    db_session.commit()
    with pytest.raises(HTTPException) as exc_info:
        unban_user(user_id="user123", db=db_session, current_user=admin)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User is not banned"


def test_unban_user_success(db_session):
    admin = Admin(id="admin123", email="admin@example.com")
    db_session.add(admin)
    user = Alumni(
        id="user123",
        email="user@example.com",
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_banned=True
    )
    db_session.add(user)
    db_session.commit()
    result = unban_user(user_id="user123", db=db_session, current_user=admin)
    assert result["message"] == "User unbanned successfully"
    db_session.refresh(user)
    assert user.is_banned is False
