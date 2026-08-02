import uuid
from datetime import datetime, timedelta

import uuid6
from sqlalchemy import String, DateTime, func, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid6.uuid7,
    )
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    admin: Mapped[bool] = mapped_column(
        default=False, server_default=expression.false()
    )

    links: Mapped[list["Link"]] = relationship("Link", back_populates="user")


class Link(Base):
    __tablename__ = "links"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid6.uuid7,
    )
    short_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    long_url: Mapped[str] = mapped_column(Text)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now() + timedelta(days=365)
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship("User", back_populates="links")
    clicks: Mapped[list["Click"]] = relationship(
        "Click",
        back_populates="link",
        cascade="all, delete-orphan"
    )


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid6.uuid7,
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    ip_address: Mapped[str] = mapped_column(String(64), index=True)
    user_agent: Mapped[str] = mapped_column(Text)
    link_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("links.id", ondelete="CASCADE")
    )

    link: Mapped["Link"] = relationship("Link", back_populates="clicks")
