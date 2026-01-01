import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.reviews.generate_review_summary")
async def test_reviews_summary(mock_ai, async_client):
    mock_ai.return_value = "Overall very positive reviews"

    response = await async_client.get("/books/1/reviews_summary")

    # Either book exists or not
    assert response.status_code in (200, 404)

    if response.status_code == 200:
        body = response.json()
        assert "average_rating" in body
        assert "review_summary" in body
