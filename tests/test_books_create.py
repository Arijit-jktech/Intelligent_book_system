import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_create_book_success(mock_ai, async_client, user_token):
    """Test successful book creation."""
    mock_ai.return_value = "Mock book summary"

    response = await async_client.post(
        "/books",
        json={
            "title": "Test Book",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["title"] == "Test Book"
    assert body["author"] == "Author"
    assert body["genre"] == "Tech"
    assert body["year_published"] == 2024
    assert body["summary"] == "Mock book summary"
    assert body["id"] is not None


@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_create_book_requires_auth(mock_ai, async_client):
    """Test that book creation requires authentication."""
    mock_ai.return_value = "Mock book summary"

    response = await async_client.post(
        "/books",
        json={
            "title": "Test Book",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        }
    )

    # Should return 403 Forbidden without authentication
    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"


@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_create_duplicate_book(mock_ai, async_client, user_token):
    """Test creating a duplicate book fails."""
    mock_ai.return_value = "Mock book summary"

    payload = {
        "title": "Duplicate Book",
        "author": "Author",
        "genre": "Tech",
        "year_published": 2024
    }

    # First creation should succeed
    resp1 = await async_client.post(
        "/books",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp1.status_code == 200, "First book creation should succeed"

    # Second creation should fail
    response = await async_client.post(
        "/books",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 409, f"Expected 409 Conflict, got {response.status_code}"
