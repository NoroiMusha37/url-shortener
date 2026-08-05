import pytest

from app.config import settings
from app.repositories.redis import RedisRepository


@pytest.mark.asyncio
async def test_cache_repository_short_code(
        redis_repo: RedisRepository
) -> None:

    # Not found
    val = await redis_repo.cache.get_short_code_by_url_hash("nonexistent")
    assert val is None

    # Set and get
    await redis_repo.cache.set_short_code_by_url_hash("hash1", "code1")
    val = await redis_repo.cache.get_short_code_by_url_hash("hash1")
    assert val == "code1"


@pytest.mark.asyncio
async def test_cache_repository_link(redis_repo: RedisRepository) -> None:

    # Not found
    val = await redis_repo.cache.get_link_id_and_url_by_short_code("nonexistent")
    assert val is None

    # Set and get
    link_id = "00000000-0000-0000-0000-000000000000"
    await redis_repo.cache.set_link_id_and_url_by_short_code(
        "code1", link_id, "http://example.com"
    )

    val = await redis_repo.cache.get_link_id_and_url_by_short_code("code1")
    assert val is not None
    assert val.id == link_id
    assert val.long_url == "http://example.com"


@pytest.mark.asyncio
async def test_rate_limiter(redis_repo: RedisRepository) -> None:
    original_limit = settings.RATE_LIMIT
    settings.RATE_LIMIT = 2

    try:
        ip_hash = "hash_ip_1"
        # 1st request
        assert await redis_repo.rate_limiter.increment_and_check(ip_hash) is True
        # 2nd request
        assert await redis_repo.rate_limiter.increment_and_check(ip_hash) is True
        # 3rd request (over limit)
        assert await redis_repo.rate_limiter.increment_and_check(ip_hash) is False

        # Another IP is unaffected
        assert await redis_repo.rate_limiter.increment_and_check("hash_ip_2") is True
    finally:
        settings.RATE_LIMIT = original_limit
