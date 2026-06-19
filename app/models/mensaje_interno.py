from __future__ import annotations
import uuid
from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class MensajeInterno(Base, TimestampMixin, TenantMixin):
    __tablename__ = "mensajes_internos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    remitente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    destinatario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    leido: Mapped[bool] = mapped_column(Boolean, default=False)
    hilo_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
