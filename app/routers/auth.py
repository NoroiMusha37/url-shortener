from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.dependencies import get_db_repo
from app.logger import Logger
from app.repositories import DBRepository
from app.schemas import Token, UserCreate, UserResponse
from app.security import verify_password, get_password_hash, create_access_token, DUMMY_HASH

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
        user_in: UserCreate, db_repo: DBRepository = Depends(get_db_repo)
):
    hashed_password = get_password_hash(user_in.password)

    Logger.info(f"Registering user with username: {user_in.username}...")
    try:
        user = await db_repo.users.create(
            username=user_in.username, 
            hashed_password=hashed_password
        )
        Logger.info("User registered successfully")
        return user
    except IntegrityError:
        Logger.error(f"User {user_in.username} already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db_repo: DBRepository = Depends(get_db_repo)
):
    user = await db_repo.users.get_by_username(username=form_data.username)

    Logger.info(f"Logging user {user.username} in...")
    if not user:
        verify_password(form_data.password, DUMMY_HASH)
        Logger.error(f"Invalid username")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        Logger.error(f"Invalid password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    Logger.info("Logged in successfully")
    return Token(access_token=access_token, token_type="bearer")
