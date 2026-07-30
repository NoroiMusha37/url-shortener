from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import LoggerMixin
from app.models import User


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


class DBRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.links = LinksRepository(session)
        self.users = UsersRepository(session)
