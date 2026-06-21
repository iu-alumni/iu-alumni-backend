from fastapi import HTTPException
import pytest

from app.api.routes.authentication.login import login
from app.core.security import get_password_hash
from app.models.users import Admin, Alumni
from app.schemas.auth import LoginRequest


def test_login_user_not_found_alumni(db_session):
    request = LoginRequest(email="nonexistent@example.com", password="password")
    with pytest.raises(HTTPException) as exc_info:
        login(request, db_session)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password"


def test_login_user_not_found_admin(db_session):
    alumni = Alumni(
        id="user123",
        email="user@example.com",
        hashed_password=get_password_hash("password"),
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_verified=True
    )
    db_session.add(alumni)
    db_session.commit()
    request = LoginRequest(email="admin@example.com", password="password")
    with pytest.raises(HTTPException) as exc_info:
        login(request, db_session)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password"


def test_login_wrong_password(db_session):
    user = Alumni(
        id="user123",
        email="user@example.com",
        hashed_password=get_password_hash("correct_password"),
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    request = LoginRequest(email="user@example.com", password="wrong_password")
    with pytest.raises(HTTPException) as exc_info:
        login(request, db_session)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password"


def test_login_user_not_verified(db_session):
    user = Alumni(
        id="user123",
        email="user@example.com",
        hashed_password=get_password_hash("password"),
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_verified=False
    )
    db_session.add(user)
    db_session.commit()
    request = LoginRequest(email="user@example.com", password="password")
    with pytest.raises(HTTPException) as exc_info:
        login(request, db_session)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Account not verified"


def test_login_user_banned(db_session):
    user = Alumni(
        id="user123",
        email="user@example.com",
        hashed_password=get_password_hash("password"),
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_verified=True,
        is_banned=True
    )
    db_session.add(user)
    db_session.commit()
    request = LoginRequest(email="user@example.com", password="password")
    with pytest.raises(HTTPException) as exc_info:
        login(request, db_session)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Account is banned"


def test_login_success_alumni(db_session, mocker):
    user = Alumni(
        id="user123",
        email="user@example.com",
        hashed_password=get_password_hash("password"),
        first_name="Test",
        last_name="User",
        graduation_year="2025",
        is_verified=True,
        is_banned=False
    )
    db_session.add(user)
    db_session.commit()
    mock_token = mocker.patch(
        "app.api.routes.authentication.login.create_access_token",
        return_value="mock_jwt_token"
    )
    request = LoginRequest(email="user@example.com", password="password")
    result = login(request, db_session)
    assert result.access_token == "mock_jwt_token"
    assert result.token_type == "bearer"
    mock_token.assert_called_once_with(data={
        "sub": user.email,
        "user_id": user.id,
        "user_type": "alumni"
    })


def test_login_success_admin(db_session, mocker):
    user = Admin(
        id="admin123",
        email="admin@example.com",
        hashed_password=get_password_hash("password")
    )
    db_session.add(user)
    db_session.commit()
    mock_token = mocker.patch(
        "app.api.routes.authentication.login.create_access_token",
        return_value="mock_jwt_token"
    )
    request = LoginRequest(email="admin@example.com", password="password")
    result = login(request, db_session)
    assert result.access_token == "mock_jwt_token"
    assert result.token_type == "bearer"
    mock_token.assert_called_once_with(data={
        "sub": user.email,
        "user_id": user.id,
        "user_type": "admin"
    })
