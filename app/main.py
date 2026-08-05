from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.config import settings
from app.exceptions import AppException, app_exception_handler
from app.middlewares import StructlogContextMiddleware
from app.repositories.redis import RedisRepository
from app.routers import auth, links


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_repo = RedisRepository(redis)

    yield {"redis_repo": redis_repo}

    await redis.aclose()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(AppException, app_exception_handler)
app.add_middleware(StructlogContextMiddleware)

app.include_router(auth.router)
app.include_router(links.router)

