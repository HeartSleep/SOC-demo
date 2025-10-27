import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication endpoints."""

    async def test_login_success(self, async_client: AsyncClient, admin_user):
        """Test successful login."""
        login_data = {
            "username": admin_user.username,
            "password": "testpass123"
        }

        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, async_client: AsyncClient, admin_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": admin_user.username,
            "password": "wrongpassword"
        }

        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }

        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    async def test_login_inactive_user(self, async_client: AsyncClient, admin_user):
        """Test login with inactive user."""
        # Deactivate user
        admin_user.is_active = False
        await admin_user.save()

        login_data = {
            "username": admin_user.username,
            "password": "testpass123"
        }

        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()

    async def test_refresh_token(self, async_client: AsyncClient, admin_user):
        """Test token refresh."""
        # First login to get tokens
        login_data = {
            "username": admin_user.username,
            "password": "testpass123"
        }

        login_response = await async_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200

        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        response = await async_client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

    async def test_get_current_user(self, async_client: AsyncClient, auth_headers, admin_user):
        """Test getting current user info."""
        response = await async_client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == admin_user.username
        assert data["email"] == admin_user.email
        assert data["full_name"] == admin_user.full_name
        assert data["role"] == admin_user.role

    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_logout(self, async_client: AsyncClient, auth_headers):
        """Test logout."""
        response = await async_client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    async def test_change_password(self, async_client: AsyncClient, auth_headers, admin_user):
        """Test password change."""
        change_data = {
            "current_password": "testpass123",
            "new_password": "newpassword123"
        }

        response = await async_client.post("/api/auth/change-password",
                                         json=change_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"

        # Test login with new password
        login_data = {
            "username": admin_user.username,
            "password": "newpassword123"
        }

        login_response = await async_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200

    async def test_change_password_wrong_current(self, async_client: AsyncClient, auth_headers):
        """Test password change with wrong current password."""
        change_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }

        response = await async_client.post("/api/auth/change-password",
                                         json=change_data, headers=auth_headers)
        assert response.status_code == 400
        assert "current password" in response.json()["detail"].lower()