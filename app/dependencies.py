from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.params import Query
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User
from app.repositories.db import DBRepository
from app.repositories.redis import RedisRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.SIGNING_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    db = DBRepository(session)
    user = await db.users.get_by_username(username=username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.admin:
        raise HTTPException(status_code=400, detail="User is not admin")
    return current_user


def get_db_repo(session: AsyncSession = Depends(get_db)) -> DBRepository:
    return DBRepository(session)


def get_redis_repo(request: Request) -> RedisRepository:
    return request.state.redis_repo


class PaginationParams:
    def __init__(
            self,
            page: int = Query(1, ge=1, le=1000),
            size: int = Query(20, ge=1, le=50)
    ):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size
