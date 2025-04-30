import pytest
from app.core.security import create_access_token

def test_login_success(client, test_alumni):
    response = client.post(
        "/auth/login",
        json={"email": "alumni@test.com", "password": "alumnipassword"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, test_alumni):
    response = client.post(
        "/auth/login",
        json={"email": "alumni@test.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@test.com", "password": "password"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password" 