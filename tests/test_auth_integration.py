"""Integration tests for authentication endpoints."""


class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""

    def test_register_endpoint_success(self, client, mocker):
        """Test successful registration via API endpoint."""
        mocker.patch("app.services.email_hash_service.is_email_allowed", return_value=True)
        mocker.patch("app.services.email_service.send_verification_link_email", return_value=True)

        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["message"].startswith("Registration successful")
        assert data["email"] == payload["email"]

    def test_register_endpoint_duplicate_email(self, client, monkeypatch):
        """Test registration with duplicate email."""
        monkeypatch.setattr("app.services.email_hash_service.is_email_allowed", lambda _: True)
        monkeypatch.setattr("app.services.email_service.send_verification_link_email", lambda *_: True)

        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "john.doe@innopolis.university",
            "telegram_alias": "johndoe",
            "password": "password123"
        }

        response1 = client.post("/api/v1/auth/register", json=payload)
        assert response1.status_code == 201

        response2 = client.post("/api/v1/auth/register", json=payload)
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "Email already registered"

    def test_register_endpoint_invalid_data(self, client):
        """Test registration with invalid data."""
        payload = {
            "first_name": "",  # Invalid: empty
            "last_name": "Doe",
            "graduation_year": "2020",
            "email": "invalid-email",
            "telegram_alias": "jd",
            "password": "123"  # Too short
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]
