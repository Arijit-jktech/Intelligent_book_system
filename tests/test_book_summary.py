import pytest

@pytest.mark.asyncio
async def test_book_summary_admin(async_client, admin_token):
    response = await async_client.get(
        "/books/1/summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code in (200, 404)
