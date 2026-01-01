import pytest

@pytest.mark.asyncio
async def test_get_all_books(async_client, user_token):
    response = await async_client.get(
        "/books",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
