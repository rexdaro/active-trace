import uuid
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from app.models.base import Base, TimestampMixin, TenantMixin
from app.models.token import RefreshToken

class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
