import pytest

@pytest.mark.asyncio
async def test_user_cannot_get_book_by_id(async_client, user_token):
    response = await async_client.get(
        "/books/1",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403
