import pytest

@pytest.mark.asyncio
async def test_get_book_admin_only(async_client, admin_token):
    response = await async_client.get(
        "/books/1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code in (200, 404)
