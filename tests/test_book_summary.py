import pytest

@pytest.mark.asyncio
async def test_book_summary_admin_only(async_client, admin_token):
    """Test that book summary endpoint requires admin role."""
    response = await async_client.get(
        "/books/1/summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Either book exists (200) or not (404), but admin access succeeds
    assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"


@pytest.mark.asyncio
async def test_book_summary_user_forbidden(async_client, user_token):
    """Test that regular users cannot get book summary."""
    response = await async_client.get(
        "/books/1/summary",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    # User should be forbidden from accessing admin endpoint
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


@pytest.mark.asyncio
async def test_book_summary_unauthenticated(async_client):
    """Test that unauthenticated users cannot get book summary."""
    response = await async_client.get("/books/1/summary")

    # Should return 401 or 403 without authentication
    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"
