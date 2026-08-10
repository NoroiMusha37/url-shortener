import json

from redis import RedisError
from redis.asyncio import Redis

from app.config import settings
from app.logger import LoggerMixin
from app.schemas import CachedLink


class CacheRepository(LoggerMixin):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def set_short_code_by_url_hash_and_user(
            self,
            url_hash: str,
            user_id: str,
            short_code: str
    ) -> None:
        self.log_info("Caching short code...")
        try:
            await self.redis.set(
                f"hash:{url_hash}:user:{user_id}",
                short_code,
                ex=settings.REDIS_CACHE_TTL
            )
        except RedisError as e:
            self.log_error("Redis error while setting short code", error=e)

    async def get_short_code_by_url_hash_and_user(
            self, url_hash: str, user_id: str
    ) -> str | None:
        self.log_info("Getting short code from cache...")
        try:
            return await self.redis.getex(
                f"hash:{url_hash}:user:{user_id}",
                ex=settings.REDIS_CACHE_TTL
            )
        except RedisError as e:
            self.log_error("Redis error while getting short code", error=e)
            return None

    async def set_link_id_and_url_by_short_code(
            self,
            short_code: str,
            link_id: str,
            long_url: str
    ):
        self.log_info("Caching link...")
        try:
            data = {"id": link_id, "long_url": long_url}
            await self.redis.set(
                f"short_code:{short_code}",
                json.dumps(data),
                ex=settings.REDIS_CACHE_TTL
            )
        except RedisError as e:
            self.log_error("Redis error while setting link", error=e)

    async def get_link_id_and_url_by_short_code(
            self,
            short_code: str
    ) -> CachedLink | None:
        self.log_info("Getting link from cache...")
        try:
            data_str = await self.redis.getex(
                f"short_code:{short_code}", ex=settings.REDIS_CACHE_TTL
            )
            if data_str:
                data = json.loads(data_str)
                return CachedLink(id=data["id"], long_url=data["long_url"])
            return None
        except RedisError as e:
            self.log_error("Redis error while getting link", error=e)
            return None

    async def invalidate_links(self, links: list[tuple[str, str, str]]):
        if not links:
            return
            
        keys_to_delete = []
        for short_code, url_hash, user_id in links:
            keys_to_delete.append(f"short_code:{short_code}")
            keys_to_delete.append(f"hash:{url_hash}:user:{user_id}")
            
        self.log_info(f"Invalidating {len(keys_to_delete)} cache keys...")
        try:
            await self.redis.delete(*keys_to_delete)
        except RedisError as e:
            self.log_error("Redis error while invalidating cache", error=e)


class RateLimiterRepository(LoggerMixin):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def increment_and_check(self, ip_hash: str) -> bool:
        key = f"rate_limit:{ip_hash}"

        async with self.redis.pipeline() as pipe:
            await pipe.incr(key)
            await pipe.expire(key, settings.RATE_LIMIT_TIME, nx=True)
            results = await pipe.execute()

        requests_count = results[0]

        if requests_count > settings.RATE_LIMIT:
            return False

        return True


class RedisRepository:
    def __init__(self, redis: Redis):
        self.cache = CacheRepository(redis)
        self.rate_limiter = RateLimiterRepository(redis)
