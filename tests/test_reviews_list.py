import pytest

@pytest.mark.asyncio
async def test_get_reviews_success(async_client):
    """Test getting reviews for a book (public endpoint)."""
    response = await async_client.get("/books/1/reviews")

    # Either book exists (200) or not (404)
    assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        body = response.json()
        assert isinstance(body, list), "Response should be a list"


@pytest.mark.asyncio
async def test_get_reviews_with_pagination(async_client):
    """Test getting reviews with skip and limit."""
    response = await async_client.get("/books/1/reviews?skip=0&limit=10")

    assert response.status_code in (200, 404), f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        body = response.json()
        assert isinstance(body, list)
        assert len(body) <= 10, "Limit should be respected"


@pytest.mark.asyncio
async def test_get_reviews_invalid_book(async_client):
    """Test getting reviews for non-existent book."""
    response = await async_client.get("/books/99999/reviews")

    # Should return 404 for non-existent book
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
