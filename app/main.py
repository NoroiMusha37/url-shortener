from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from redis.asyncio import Redis

from app.config import settings
from app.exceptions import AppException, app_exception_handler
from app.ipapi_client import IPAPIClient
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

    httpx_client = httpx.AsyncClient()
    ip_api_client = IPAPIClient(httpx_client)

    yield {
        "redis_repo": redis_repo,
        "ip_api_client": ip_api_client,
    }

    await redis.aclose()
    await httpx_client.aclose()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(AppException, app_exception_handler)
app.add_middleware(StructlogContextMiddleware)

app.include_router(auth.router)
app.include_router(links.router)
