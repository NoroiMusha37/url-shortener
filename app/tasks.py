import asyncio
from redis.asyncio import Redis

from app.celery_app import celery_app
from app.config import settings
from app.logger import Logger
from app.repositories.db import DBRepository
from app.repositories.redis import RedisRepository
from app.database import AsyncSessionLocal, engine


async def _delete_expired_links_async():
    try:
        async with AsyncSessionLocal() as session:
            db_repo = DBRepository(session)
            deleted_links = await db_repo.links.delete_expired()
            
            if deleted_links:
                redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
                redis_repo = RedisRepository(redis)
                await redis_repo.cache.invalidate_links(deleted_links)
                await redis.aclose()
                
            return len(deleted_links)
    finally:
        await engine.dispose()


@celery_app.task(bind=True)
def delete_expired_links(self):
    Logger.info(f"Executing task {self.request.id}...")
    deleted_count = asyncio.run(_delete_expired_links_async())
    Logger.info(f"Deleted {deleted_count} expired links")

    return deleted_count
