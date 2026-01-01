import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_create_book(mock_ai, async_client, user_token):
    mock_ai.return_value = "Mock book summary"

    response = await async_client.post(
        "/books",
        json={
            "title": "Test Book",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Test Book"
    assert body["summary"] == "Mock book summary"
