from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.base import Base

# In-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    echo=False
)

AsyncSessionTest = sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_test_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
