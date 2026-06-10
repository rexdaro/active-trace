import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, JSON, Integer
from app.models.base import Base, TimestampMixin

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    impersonator_id: Mapped[str] = mapped_column(String, nullable=True)
    materia_id: Mapped[str] = mapped_column(String, nullable=True)
    detalle: Mapped[dict] = mapped_column(JSON, nullable=False)
    filas_afectadas: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(String, nullable=True)
    user_agent: Mapped[str] = mapped_column(String, nullable=True)
