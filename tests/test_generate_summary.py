import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_generate_summary_admin_success(mock_ai, async_client, admin_token):
    """Test successful summary generation by admin."""
    mock_ai.return_value = "Generated summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["summary"] == "Generated summary"


@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_generate_summary_user_forbidden(mock_ai, async_client, user_token):
    """Test that regular users cannot generate summaries."""
    mock_ai.return_value = "Generated summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    # User should be forbidden from generating summaries
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


@pytest.mark.asyncio
@patch("app.api.routes.books.generate_book_summary")
async def test_generate_summary_unauthenticated(mock_ai, async_client):
    """Test that unauthenticated users cannot generate summaries."""
    mock_ai.return_value = "Generated summary"

    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"}
    )

    # Should return 401 or 403 without authentication
    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"
