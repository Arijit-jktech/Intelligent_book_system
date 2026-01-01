import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.services.ai_service.generate_book_summary")
async def test_add_review(mock_ai, async_client, user_token):
    # Create book first
    mock_ai.return_value = "Mock summary"
    book_resp = await async_client.post(
        "/books",
        json={
            "title": "Book For Review",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    book_id = book_resp.json()["id"]

    # Add review
    response = await async_client.post(
        f"/books/{book_id}/reviews",
        json={
            "review_text": "Excellent book",
            "rating": 5
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Review added"
