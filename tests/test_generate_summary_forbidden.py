import pytest

@pytest.mark.asyncio
async def test_generate_summary_user_forbidden(async_client, user_token):
    response = await async_client.post(
        "/generate-summary",
        json={"title": "Some Book"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403
