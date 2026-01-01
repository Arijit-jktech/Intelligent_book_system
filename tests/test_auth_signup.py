import pytest

@pytest.mark.asyncio
async def test_signup_success(async_client):
    response = await async_client.post(
        "/auth/signup",
        json={
            "username": "new_user_1",
            "password": "password123",
            "role": "user"
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "new_user_1"
    assert body["role"] == "user"
    assert "password" not in body  # security check


@pytest.mark.asyncio
async def test_signup_duplicate_user(async_client):
    payload = {
        "username": "duplicate_user",
        "password": "password123",
        "role": "user"
    }

    # First signup
    await async_client.post("/auth/signup", json=payload)

    # Second signup (should fail)
    response = await async_client.post("/auth/signup", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"
