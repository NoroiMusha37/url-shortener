import uuid
from datetime import timedelta

from sqlalchemy import select, func, Sequence, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import LoggerMixin
from app.models import User, Link, Click
from app.schemas import PaginationParams


class UsersRepository(LoggerMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)

        self.log_info("Getting user by username...")
        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error(
                "DB query failed while trying to get user by username", error=e
            )
            raise

    async def create(self, username: str, hashed_password: str) -> User:
        user = User(username=username, hashed_password=hashed_password)
        self.session.add(user)

        self.log_info("Creating user...")
        try:
            await self.session.commit()
            return user
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to create user", error=e)
            await self.session.rollback()
            raise


class LinksRepository(LoggerMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_short_code_by_url_hash_and_user(
            self, url_hash: str, user_id: str
    ) -> str | None:
        stmt = (
            select(Link.short_code)
            .where(Link.url_hash == url_hash, Link.user_id == user_id)
        )
        self.log_info("Getting link by url hash...")

        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get link", error=e)
            raise

    async def get_by_short_code(self, short_code: str) -> Link | None:
        stmt = select(Link).where(
            Link.short_code == short_code,
            Link.expires_at > func.now()
        )
        self.log_info("Getting url by short code...")

        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get url", error=e)
            raise

    async def upsert(
            self, short_code: str, long_url: str, url_hash: str, user_id: str
    ) -> str | None:
        stmt = (insert(Link)
                .values(
            short_code=short_code,
            long_url=long_url,
            url_hash=url_hash,
            user_id=user_id,
        )
                .on_conflict_do_update(
            index_elements=["url_hash", "user_id"],
            set_={"expires_at": func.now() + timedelta(days=365)},
            where=(Link.expires_at < func.now() + timedelta(days=364))
        )
                .returning(Link.short_code)
                )

        self.log_info("Upserting link...")
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to upsert link", error=e)
            await self.session.rollback()
            raise

    async def get_user_links_count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Link.id)).where(Link.user_id == user_id)

        self.log_info("Getting user's links count...")
        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get user links count", error=e)
            await self.session.rollback()
            raise

    async def get_paginated_list(
            self, user_id: uuid.UUID, params: PaginationParams
    ) -> Sequence[Link]:
        stmt = (
            select(Link)
            .where(Link.user_id == user_id)
            .order_by(Link.expires_at.asc())
            .offset(params.offset)
            .limit(params.size)
        )

        self.log_info("Getting paginated links...")
        try:
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get paginated links", error=e)
            await self.session.rollback()
            raise

    async def delete_expired(self) -> list[tuple[str, str, str]]:
        stmt = (
            delete(Link)
            .where(Link.expires_at < func.now())
            .returning(Link.url_hash, Link.user_id, Link.short_code)
        )

        self.log_info("Deleting expired links...")
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            return [
                (row.url_hash, str(row.user_id), row.short_code)
                for row in result.all()
            ]
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to delete expired links", error=e)
            await self.session.rollback()
            raise


class ClicksRepository(LoggerMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            ip_address: str,
            user_agent: str,
            referer: str | None,
            link_id: uuid.UUID
    ) -> Click:
        click = Click(
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            link_id=link_id,
        )
        self.session.add(click)

        self.log_info("Creating click...")
        try:
            await self.session.commit()
            return click
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to create click", error=e)
            await self.session.rollback()
            raise

    async def get_total_clicks(self, short_code: str) -> int:
        stmt = (
            select(func.count(Click.id))
            .join(Link)
            .where(Link.short_code == short_code)
        )

        self.log_info("Getting total clicks...")
        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get total clicks", error=e)
            await self.session.rollback()
            raise

    async def get_last_24_hours_clicks(self, short_code: str) -> int:
        stmt = (
            select(func.count(Click.id))
            .join(Link)
            .where(
                Link.short_code == short_code,
                Click.clicked_at > func.now() - timedelta(hours=24))
        )

        self.log_info("Getting last 24 hours clicks...")
        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get last 24 hours clicks", error=e)
            await self.session.rollback()
            raise

    async def get_top_referrers(
            self, short_code: str, count: int
    ) -> dict[str, int]:
        stmt = (
            select(Click.referer, func.count(Click.id).label("clicks_count"))
            .join(Link)
            .where(Link.short_code == short_code)
            .group_by(Click.referer)
            .order_by(func.count(Click.id).desc())
            .limit(count)
        )

        self.log_info(f"Getting top {count} referrers...")
        try:
            result = await self.session.execute(stmt)
            return {
                (row.referer if row.referer is not None else "Direct"): row.clicks_count
                for row in result.all()
            }
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get top referrers", error=e)
            await self.session.rollback()
            raise

    async def get_top_ips(
            self, short_code: str, count: int
    ) -> dict[str, int]:
        stmt = (
            select(Click.ip_address, func.count(Click.id).label("clicks_count"))
            .join(Link)
            .where(Link.short_code == short_code)
            .group_by(Click.ip_address)
            .order_by(func.count(Click.id).desc())
            .limit(count)
        )

        self.log_info(f"Getting top {count} ips...")
        try:
            result = await self.session.execute(stmt)
            ips = {}
            for row in result.all():
                if row.ip_address is not None:
                    ips[row.ip_address] = row.clicks_count

            return ips
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get top ips", error=e)
            await self.session.rollback()
            raise


class DBRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.links = LinksRepository(session)
        self.users = UsersRepository(session)
        self.clicks = ClicksRepository(session)
