import pytest

@pytest.mark.asyncio
async def test_get_all_books_success(async_client, user_token):
    """Test getting all books with valid token."""
    response = await async_client.get(
        "/books",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert isinstance(body, list), "Response should be a list"


@pytest.mark.asyncio
async def test_get_all_books_requires_auth(async_client):
    """Test that getting all books requires authentication."""
    response = await async_client.get("/books")

    # Should return 401 or 403 without authentication
    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"


@pytest.mark.asyncio
async def test_get_books_with_pagination(async_client, user_token):
    """Test getting books with skip and limit parameters."""
    response = await async_client.get(
        "/books?skip=0&limit=5",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    body = response.json()
    assert isinstance(body, list)
    # Limit should be respected (at most 5 items)
    assert len(body) <= 5
