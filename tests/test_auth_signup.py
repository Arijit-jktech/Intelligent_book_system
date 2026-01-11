import pytest

@pytest.mark.asyncio
async def test_signup_success(async_client):
    """Test successful user signup."""
    response = await async_client.post(
        "/auth/signup",
        json={
            "username": "new_user_1",
            "password": "password123",
            "role": "user"
        }
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["username"] == "new_user_1"
    assert body["role"] == "user"
    assert body["id"] is not None
    assert "password" not in body  # security check - password should never be returned


@pytest.mark.asyncio
async def test_signup_duplicate_user(async_client):
    """Test that duplicate username signup fails."""
    payload = {
        "username": "duplicate_user",
        "password": "password123",
        "role": "user"
    }

    # First signup
    resp1 = await async_client.post("/auth/signup", json=payload)
    assert resp1.status_code == 200, "First signup should succeed"

    # Second signup (should fail)
    response = await async_client.post("/auth/signup", json=payload)

    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    body = response.json()
    assert "detail" in body
