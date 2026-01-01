import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_generate_summary_admin(mock_ai, async_client, admin_token):
    mock_ai.return_value = "Generated summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "Generated summary"
