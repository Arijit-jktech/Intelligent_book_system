import pytest

@pytest.mark.asyncio
async def test_generate_summary_user_forbidden(async_client, user_token):
    """Test that non-admin users cannot generate summaries."""
    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    body = response.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_generate_summary_no_auth(async_client):
    """Test that unauthenticated users cannot generate summaries."""
    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"}
    )

    assert response.status_code in (401, 403), f"Expected auth error, got {response.status_code}"
