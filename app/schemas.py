import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


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


class LinkResponse(BaseModel):
    short_code: str
    original_url: HttpUrl
