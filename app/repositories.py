from datetime import timedelta

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import LoggerMixin
from app.models import User, Link


class UsersRepository(LoggerMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str):
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

    async def create(self, username: str, hashed_password: str):
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

    async def get_short_code_by_url_hash(self, url_hash: str):
        stmt = select(Link.short_code).where(Link.url_hash == url_hash)
        self.log_info("Getting link by url hash...")

        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.log_error("DB query failed while trying to get link", error=e)
            raise

    async def upsert(
            self, short_code: str, long_url: str, url_hash: str, user_id: str
    ):
        stmt = (insert(Link)
                .values(
            short_code=short_code,
            long_url=long_url,
            url_hash=url_hash,
            user_id=user_id,
        )
                .on_conflict_do_update(
            index_elements=["url_hash"],
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


class DBRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.links = LinksRepository(session)
        self.users = UsersRepository(session)
