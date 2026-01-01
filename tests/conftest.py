import sys
import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db.session import get_db
from tests.db_test import AsyncSessionTest, init_test_db

# ---------------- DB OVERRIDE ---------------- #

async def override_get_db():
    async with AsyncSessionTest() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    await init_test_db()

# ---------------- CLIENT ---------------- #

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

# ---------------- AUTH FIXTURES ---------------- #

@pytest_asyncio.fixture
async def signup_user(async_client):
    payload = {
        "username": "test_user",
        "password": "password123",
        "role": "user"
    }
    res = await async_client.post("/auth/signup", json=payload)
    if res.status_code not in (200, 400):
        raise RuntimeError(res.text)
    return payload


@pytest_asyncio.fixture
async def signup_admin(async_client):
    payload = {
        "username": "admin_user",
        "password": "admin123",
        "role": "admin"
    }
    res = await async_client.post("/auth/signup", json=payload)
    if res.status_code not in (200, 400):
        raise RuntimeError(res.text)
    return payload


@pytest_asyncio.fixture
async def user_token(async_client, signup_user):
    res = await async_client.post(
        "/auth/login",
        json={
            "username": signup_user["username"],
            "password": signup_user["password"]
        }
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(async_client, signup_admin):
    res = await async_client.post(
        "/auth/login",
        json={
            "username": signup_admin["username"],
            "password": signup_admin["password"]
        }
    )
    assert res.status_code == 200
    return res.json()["access_token"]
# ---------------- CLEANUP ---------------- #