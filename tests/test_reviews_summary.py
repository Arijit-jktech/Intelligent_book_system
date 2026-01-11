import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.routes.reviews.generate_review_summary")
async def test_reviews_summary_requires_admin(mock_ai, async_client):
    """Test that reviews_summary endpoint requires admin authentication."""
    mock_ai.return_value = "Overall very positive reviews"

    # Should fail without authentication
    response = await async_client.get("/books/1/reviews_summary")
    assert response.status_code == 403  # Forbidden (not authenticated)


@pytest.mark.asyncio
@patch("app.api.routes.reviews.generate_review_summary")
async def test_reviews_summary_with_admin_auth(mock_ai, async_client, admin_token):
    """Test that reviews_summary endpoint works with admin token."""
    mock_ai.return_value = "Overall very positive reviews"

    response = await async_client.get(
        "/books/1/reviews_summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Either book exists or not, but auth should pass
    assert response.status_code in (200, 404)

    if response.status_code == 200:
        body = response.json()
        assert "average_rating" in body
        assert "review_summary" in body


@pytest.mark.asyncio
@patch("app.api.routes.reviews.generate_review_summary")
async def test_reviews_summary_user_forbidden(mock_ai, async_client, user_token):
    """Test that regular users cannot access reviews_summary."""
    mock_ai.return_value = "Overall very positive reviews"

    response = await async_client.get(
        "/books/1/reviews_summary",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # User should be forbidden from accessing this admin endpoint
    assert response.status_code == 403

