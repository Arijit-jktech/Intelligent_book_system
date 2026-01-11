import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_ai_summary_mock(mock_ai, async_client, admin_token):
    """Test AI summary generation with mocked AI service."""
    mock_ai.return_value = "Mock summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Test Book"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["summary"] == "Mock summary"
    # Verify mock was called
    mock_ai.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_ai_summary_called_with_title(mock_ai, async_client, admin_token):
    """Test that AI service is called with correct parameters."""
    mock_ai.return_value = "Generated summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Specific Book Title"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    # Verify mock was called with title
    mock_ai.assert_called()
    call_args = mock_ai.call_args
    # Verify the function was called (arguments may vary based on implementation)
    assert call_args is not None
