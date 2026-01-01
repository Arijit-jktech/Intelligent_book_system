import pytest

@pytest.mark.asyncio
async def test_reviews_summary_book_not_found(async_client):
    response = await async_client.get("/books/99999/reviews_summary")

    assert response.status_code == 404
