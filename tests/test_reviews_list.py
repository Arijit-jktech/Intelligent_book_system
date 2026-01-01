import pytest

@pytest.mark.asyncio
async def test_get_reviews(async_client):
    response = await async_client.get("/books/1/reviews")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
