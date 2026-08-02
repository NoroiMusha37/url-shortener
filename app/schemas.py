import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, HttpUrl

from app.config import settings

ShortCodePath = Annotated[
    str,
    Path(
        ...,
        min_length=settings.SHORT_CODE_LENGTH,
        max_length=settings.SHORT_CODE_LENGTH
    )
]


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime
    admin: bool

    model_config = ConfigDict(from_attributes=True)


class LinkRequest(BaseModel):
    url: HttpUrl


class BaseLink(BaseModel):
    short_code: str
    original_url: HttpUrl


class LinkResponse(BaseLink):
    pass


class LinkObject(BaseLink):
    expires_at: datetime


class LinkStatsResponse(BaseModel):
    total_clicks: int
    last_24_hours_clicks: int
    top_referrers: dict[str, int]


class LinksListResponse(BaseModel):
    links: list[LinkObject]
    page: int
    size: int
    pages: int
    total: int
