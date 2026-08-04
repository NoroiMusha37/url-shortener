import asyncio
from math import ceil

from fastapi import (
    APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
)
from sqlalchemy.exc import IntegrityError
from starlette.responses import RedirectResponse

from app.config import settings
from app.dependencies import (
    get_db_repo, get_current_user, get_current_admin_user,
    PaginationParams, get_redis_repo, rate_limiter
)
from app.logger import Logger
from app.models import User
from app.repositories.db import DBRepository
from app.repositories.redis import RedisRepository
from app.schemas import (
    LinkResponse, LinkRequest, ShortCodePath,
    LinkStatsResponse, LinksListResponse
)
from app.service import (
    hash_str, normalize_url, generate_short_code,
    truncate_ip, get_link_by_short_code
)

router = APIRouter(tags=["Links"], dependencies=[Depends(rate_limiter)])


@router.post(
    "/links", 
    response_model=LinkResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_short_code(
        data_in: LinkRequest,
        db_repo: DBRepository = Depends(get_db_repo),
        redis_repo: RedisRepository = Depends(get_redis_repo),
        current_user=Depends(get_current_user)
):
    Logger.info(f"Shortening url {data_in.url}...")
    hashed_url = hash_str(normalize_url(str(data_in.url)))

    short_code = await redis_repo.cache.get_short_code_by_url_hash(hashed_url)

    if short_code:
        Logger.info("Cache hit")
        return LinkResponse(short_code=short_code, original_url=data_in.url)

    Logger.info("Cache missed")
    for _ in range(settings.RETRIES_NUM):
        new_code = generate_short_code(settings.SHORT_CODE_LENGTH)

        try:
            short_code = await db_repo.links.upsert(
                short_code=new_code,
                long_url=str(data_in.url),
                url_hash=hashed_url,
                user_id=current_user.id
            )
        except IntegrityError:
            continue

        if not short_code:
            short_code = await db_repo.links.get_short_code_by_url_hash(hashed_url)

        await redis_repo.cache.set_short_code_by_url_hash(hashed_url, short_code)
        
        return LinkResponse(short_code=short_code, original_url=data_in.url)

    Logger.error(f"Hit collision {settings.RETRIES_NUM} times for {data_in.url}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Collision: cannot generate short code"
    )


@router.get("/{short_code}")
async def get_short_code(
        short_code: ShortCodePath,
        request: Request,
        background_tasks: BackgroundTasks,
        db_repo: DBRepository = Depends(get_db_repo),
        redis_repo: RedisRepository = Depends(get_redis_repo),
):
    Logger.info("Redirecting...")

    link = await redis_repo.cache.get_link_id_and_url_by_short_code(short_code)

    if link is None:
        Logger.info("Cache missed")
        link = await get_link_by_short_code(short_code, db_repo)
        
        await redis_repo.cache.set_link_id_and_url_by_short_code(
            short_code, 
            str(link.id), 
            link.long_url
        )
    else:
        Logger.info("Cache hit")

    raw_ip = request.client.host if request.client else ""

    background_tasks.add_task(
        db_repo.clicks.create,
        ip_address=truncate_ip(raw_ip),
        user_agent=request.headers.get("user-agent", ""),
        referer=request.headers.get("referer"),
        link_id=link.id
    )

    Logger.info("Redirected successfully")
    return RedirectResponse(
        url=link.long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.get(
    "/{short_code}/stats",
    response_model=LinkStatsResponse,
    dependencies=[Depends(get_current_admin_user)]
)
async def get_link_stats(
        short_code: ShortCodePath,
        db_repo: DBRepository = Depends(get_db_repo)
):
    Logger.info("Calculating stats...")

    _ = await get_link_by_short_code(short_code, db_repo)

    total_clicks, last_24_hours_clicks, top_referrers = await asyncio.gather(
        db_repo.clicks.get_total_clicks(short_code),
        db_repo.clicks.get_last_24_hours_clicks(short_code),
        db_repo.clicks.get_top_referrers(short_code, settings.TOP_REFERRERS)
    )

    return LinkStatsResponse(
        total_clicks=total_clicks,
        last_24_hours_clicks=last_24_hours_clicks,
        top_referrers=top_referrers
    )


@router.get("/links", response_model=LinksListResponse)
async def get_links(
        db_repo: DBRepository = Depends(get_db_repo),
        current_user: User = Depends(get_current_user),
        params: PaginationParams = Depends()
):
    Logger.info("Getting paginated links list...")

    links, count = await asyncio.gather(
        db_repo.links.get_paginated_list(current_user.id, params),
        db_repo.links.get_user_links_count(current_user.id)
    )

    return LinksListResponse(
        links=links,
        page=params.page,
        size=params.size,
        pages=ceil(count / params.size),
        total=count
    )
