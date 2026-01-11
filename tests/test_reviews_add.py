import pytest
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.services.ai_service.generate_book_summary")
async def test_add_review_success(mock_ai, async_client, user_token):
    """Test successfully adding a review to a book."""
    mock_ai.return_value = "Mock summary"
    
    # Create book first
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
    assert book_resp.status_code == 200
    book_id = book_resp.json()["id"]

    # Add review
    response = await async_client.post(
        f"/books/{book_id}/reviews",
        json={
            "review_text": "Excellent book with great content",
            "rating": 5
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    body = response.json()
    assert "message" in body
    assert "review_id" in body


@pytest.mark.asyncio
@patch("app.services.ai_service.generate_book_summary")
async def test_add_review_requires_auth(mock_ai, async_client):
    """Test that adding review requires authentication."""
    mock_ai.return_value = "Mock summary"

    response = await async_client.post(
        "/books/1/reviews",
        json={
            "review_text": "Great book",
            "rating": 5
        }
    )

    # Should return 401 or 403 without authentication
    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"


@pytest.mark.asyncio
@patch("app.services.ai_service.generate_book_summary")
async def test_add_review_invalid_rating(mock_ai, async_client, user_token):
    """Test that invalid rating is rejected."""
    mock_ai.return_value = "Mock summary"
    
    # Create book first
    book_resp = await async_client.post(
        "/books",
        json={
            "title": "Book For Invalid Review",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    book_id = book_resp.json()["id"]

    # Try to add review with invalid rating
    response = await async_client.post(
        f"/books/{book_id}/reviews",
        json={
            "review_text": "Good book",
            "rating": 10  # Invalid - should be 1-5
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    # Should reject invalid rating
    assert response.status_code in (400, 422), f"Expected validation error, got {response.status_code}"


@pytest.mark.asyncio
@patch("app.services.ai_service.generate_book_summary")
async def test_add_review_short_text(mock_ai, async_client, user_token):
    """Test that too-short review text is rejected."""
    mock_ai.return_value = "Mock summary"
    
    # Create book
    book_resp = await async_client.post(
        "/books",
        json={
            "title": "Book For Short Review",
            "author": "Author",
            "genre": "Tech",
            "year_published": 2024
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    book_id = book_resp.json()["id"]

    # Try to add review with too-short text
    response = await async_client.post(
        f"/books/{book_id}/reviews",
        json={
            "review_text": "Good",  # Too short
            "rating": 5
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    # Should reject short text
    assert response.status_code in (400, 422), f"Expected validation error, got {response.status_code}"
