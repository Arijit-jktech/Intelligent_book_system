import pytest

@pytest.mark.asyncio
async def test_user_cannot_get_book_by_id(async_client, user_token):
    """Test that regular users cannot get single book details (admin only)."""
    response = await async_client.get(
        "/books/1",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


@pytest.mark.asyncio
async def test_admin_can_get_book_by_id(async_client, admin_token):
    """Test that admins can get book details."""
    response = await async_client.get(
        "/books/1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Either book exists (200) or not (404), but not 403
    assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"


@pytest.mark.asyncio
async def test_user_can_create_book(async_client, user_token):
    """Test that regular users can create books."""
    from unittest.mock import patch
    with patch("app.api.routes.books.generate_book_summary", return_value="Test summary"):
        response = await async_client.post(
            "/books",
            json={
                "title": "User Book",
                "author": "User Author",
                "genre": "Tech",
                "year_published": 2024
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
