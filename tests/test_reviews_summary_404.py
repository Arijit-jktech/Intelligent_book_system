import pytest

@pytest.mark.asyncio
async def test_reviews_summary_book_not_found_no_auth(async_client):
    """Test that endpoint requires authentication before checking if book exists."""
    response = await async_client.get("/books/99999/reviews_summary")

    # Should get 403 Forbidden (auth error) before 404 (book not found)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reviews_summary_book_not_found_with_auth(async_client, admin_token):
    """Test that endpoint returns 404 for non-existent book when authenticated."""
    response = await async_client.get(
        "/books/99999/reviews_summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404

