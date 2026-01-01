import pytest

@pytest.mark.asyncio
async def test_login_success(async_client, signup_user):
    response = await async_client.post(
        "/auth/login",
        json={
            "username": signup_user["username"],
            "password": signup_user["password"]
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client, signup_user):
    response = await async_client.post(
        "/auth/login",
        json={
            "username": signup_user["username"],
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
