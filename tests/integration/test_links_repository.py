import datetime

import pytest
from sqlalchemy import insert
from sqlalchemy.sql import func

from app.models import Link
from app.repositories.db import LinksRepository, UsersRepository
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_links_repository_upsert_new(db_session: AsyncSession) -> None:
    repo = LinksRepository(db_session)

    users_repo = UsersRepository(db_session)
    user = await users_repo.create(username="testuser", hashed_password="pwd")

    short_code = await repo.upsert(
        short_code="newcode",
        long_url="http://example.com",
        url_hash="hash1",
        user_id=str(user.id),
    )

    assert short_code == "newcode"

    link = await repo.get_by_short_code("newcode")
    assert link is not None
    assert link.long_url == "http://example.com"


@pytest.mark.asyncio
async def test_links_repository_upsert_conflict_expired(
    db_session: AsyncSession
) -> None:
    repo = LinksRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await users_repo.create(
        username="testuser2",
        hashed_password="pwd"
    )

    # 1. Insert a link that has 10 days left
    stmt = (
        insert(Link)
        .values(
            short_code="oldcode",
            long_url="http://example.com",
            url_hash="hash2",
            user_id=user.id,
            expires_at=func.now() + datetime.timedelta(days=10),
        )
        .returning(Link.expires_at)
    )
    result = await db_session.execute(stmt)
    old_expires_at = result.scalar_one()
    await db_session.commit()

    # 2. Upsert same url_hash -> it should update expires_at because 10 days < 364 days
    short_code = await repo.upsert(
        short_code="newcode",
        long_url="http://example.com",
        url_hash="hash2",
        user_id=str(user.id),
    )

    assert short_code == "oldcode"

    # Verify expires_at was updated
    link = await repo.get_by_short_code("oldcode")
    assert link.expires_at > old_expires_at


@pytest.mark.asyncio
async def test_links_repository_upsert_conflict_fresh(
    db_session: AsyncSession
) -> None:
    repo = LinksRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await users_repo.create(
        username="testuser3",
        hashed_password="pwd"
    )

    # 1. Insert a fresh link
    old_code = await repo.upsert(
        short_code="freshcd",
        long_url="http://example.com",
        url_hash="hash3",
        user_id=str(user.id),
    )

    # 2. Upsert same url_hash. Because it's fresh (expires_at >= now + 364),
    # the WHERE clause prevents update.
    short_code = await repo.upsert(
        short_code="newcode",
        long_url="http://example.com",
        url_hash="hash3",
        user_id=str(user.id),
    )

    assert short_code is None
