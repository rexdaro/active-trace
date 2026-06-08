import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.models.base import Base, TimestampMixin

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
