from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.config import settings
from app.middlewares import StructlogContextMiddleware
from app.routers import auth, links


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2
    )

    yield {"redis": redis}

    await redis.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(StructlogContextMiddleware)

app.include_router(auth.router)
app.include_router(links.router)
