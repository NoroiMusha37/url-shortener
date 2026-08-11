from arq import cron
from redis.asyncio import Redis

from app import config
from app.database import AsyncSessionLocal, engine
from app.logger import Logger
from app.repositories.db import DBRepository
from app.repositories.redis import RedisRepository


async def delete_expired_links(ctx) -> int:
    redis_repo = ctx["redis_repo"]
    async with AsyncSessionLocal() as session:
        db_repo = DBRepository(session)
        deleted_links = await db_repo.links.delete_expired()
        await redis_repo.cache.invalidate_links(deleted_links)

        Logger.info(f"Deleted {len(deleted_links)} expired links")
        return len(deleted_links)


async def startup(ctx):
    redis = Redis.from_url(
        config.settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2
    )
    ctx["redis_client"] = redis
    ctx["redis_repo"] = RedisRepository(redis)


async def shutdown(ctx):
    if "redis_client" in ctx:
        await ctx["redis_client"].aclose()

    await engine.dispose()


class WorkerSettings:
    cron_jobs = [
        cron(delete_expired_links, hour=3)  # type: ignore
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = config.REDIS_SETTINGS
    keep_result = 60 * 60 * 24
