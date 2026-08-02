import asyncio

from fastapi import (
    APIRouter, Depends, HTTPException, BackgroundTasks, Request
)
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.responses import RedirectResponse

from app.config import settings
from app.dependencies import get_db_repo, get_current_user, get_current_admin_user
from app.logger import Logger
from app.models import User
from app.repositories import DBRepository
from app.schemas import LinkResponse, LinkRequest, ShortCodePath, LinkStatsResponse
from app.service import (
    hash_url, normalize_url, generate_short_code, truncate_ip
)

router = APIRouter(tags=["links"])


@router.post(
    "/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED
)
async def create_short_code(
        data_in: LinkRequest,
        db_repo: DBRepository = Depends(get_db_repo),
        current_user=Depends(get_current_user)
):
    Logger.info(f"Shortening url {data_in.url}...")
    hashed_url = hash_url(normalize_url(str(data_in.url)))

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
        db_repo: DBRepository = Depends(get_db_repo)
):
    Logger.info("Redirecting...")
    link = await db_repo.links.get_by_short_code(short_code)

    if not link:
        Logger.error(f"Url with short code {short_code} either expired or didn't exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )

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


@router.get("/{short_code}/stats", response_model=LinkStatsResponse)
async def get_link_stats(
        short_code: ShortCodePath,
        db_repo: DBRepository = Depends(get_db_repo),
        admin: User = Depends(get_current_admin_user)
):
    Logger.info("Calculating stats...")
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
