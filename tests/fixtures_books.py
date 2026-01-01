import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.services.ai_service.generate_book_summary")
async def create_test_book(mock_ai, async_client, admin_token):
    mock_ai.return_value = "Test book summary"

    response = await async_client.post(
        "/books",
        json={
            "title": "Review Test Book",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    return response.json()["id"]
