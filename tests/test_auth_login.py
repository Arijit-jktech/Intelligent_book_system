import pytest

@pytest.mark.asyncio
async def test_login_success(async_client, signup_user):
    """Test successful login."""
    response = await async_client.post(
        "/auth/login",
        json={
            "username": signup_user["username"],
            "password": signup_user["password"]
        }
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert "access_token" in body, "Response should contain access_token"
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client, signup_user):
    """Test login with invalid password."""
    response = await async_client.post(
        "/auth/login",
        json={
            "username": signup_user["username"],
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    body = response.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client):
    """Test login with non-existent user."""
    response = await async_client.post(
        "/auth/login",
        json={
            "username": "nonexistent_user",
            "password": "password123"
        }
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    body = response.json()
    assert "detail" in body
