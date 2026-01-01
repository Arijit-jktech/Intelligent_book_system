import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_ai_summary_mock(mock_ai, async_client, admin_token):
    mock_ai.return_value = "Mock summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Test Book"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "Mock summary"
