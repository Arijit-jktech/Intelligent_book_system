import pytest

@pytest.mark.asyncio
async def test_add_review_unauthorized(async_client):
    response = await async_client.post(
        "/books/1/reviews",
        json={"review_text": "Nice", "rating": 4}
    )

    assert response.status_code == 401
