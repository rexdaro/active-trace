import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from app.models.base import Base, TimestampMixin

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    moodle_ws_url: Mapped[str | None] = mapped_column(String, nullable=True)
    moodle_token: Mapped[str | None] = mapped_column(String, nullable=True)
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
