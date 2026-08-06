import asyncio
import os
from typing import AsyncGenerator

import asyncpg

# Override env vars before importing anything from the app
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/url_shortener_test"
)
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET_KEY"] = "testsecret_must_be_32_bytes_long_123"

# --- CI/CD Config ---
# os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/url_shortener_test")
# os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.database import Base, get_db
from app.dependencies import get_redis_repo, get_ip_api_client
from app.main import app
from app.repositories.redis import RedisRepository


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create an instance of the default event loop for each testcase."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    # Connect to the default postgres database to create the test DB
    try:
        sys_conn = await asyncpg.connect(
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432,
            database="postgres",
        )
        await sys_conn.execute("DROP DATABASE IF EXISTS url_shortener_test")
        await sys_conn.execute("CREATE DATABASE url_shortener_test")
        await sys_conn.close()
    except Exception as e:
        print(
            "Warning: Could not recreate test DB. It may already exist or "
            f"Postgres is unreachable. Error: {e}"
        )

    engine = create_async_engine(settings.DATABASE_URL)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(settings.DATABASE_URL)
    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    # Truncate tables before each test
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE;"))

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def redis_repo() -> AsyncGenerator[RedisRepository, None]:
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis.flushdb()
    repo = RedisRepository(redis)
    yield repo
    await redis.aclose()


class MockIPAPIClient:
    async def get_country(self, ip: str) -> str:
        return "Unknown"

    async def get_ips_data(self, ips: list[str]) -> list[dict]:
        return [{"query": ip, "country": "Test Country", "regionName": "Test Region", "city": "Test City"} for ip in ips]


@pytest_asyncio.fixture(scope="function")
async def client(
        db_session: AsyncSession, redis_repo: RedisRepository
) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_repo] = lambda: redis_repo
    app.dependency_overrides[get_ip_api_client] = lambda: MockIPAPIClient()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
