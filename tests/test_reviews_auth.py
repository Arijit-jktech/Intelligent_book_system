import pytest

@pytest.mark.asyncio
async def test_add_review_unauthorized(async_client):
    """Test that adding review without authentication fails."""
    response = await async_client.post(
        "/books/1/reviews",
        json={"review_text": "Nice book with good content", "rating": 4}
    )

    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"


@pytest.mark.asyncio
async def test_get_reviews_public(async_client):
    """Test that getting reviews is public (no auth required)."""
    response = await async_client.get("/books/1/reviews")

    # Public endpoint - should return 200 if book exists, 404 otherwise
    assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"
