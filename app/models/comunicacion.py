from __future__ import annotations
import uuid
import os
from datetime import datetime
import enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin
from app.core.security import encrypt, decrypt


class ComunicacionEstado(str, enum.Enum):
    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"


class Comunicacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "comunicaciones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    enviado_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    _destinatario: Mapped[str] = mapped_column("destinatario", String, nullable=False)
    asunto: Mapped[str] = mapped_column(String, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String, default=ComunicacionEstado.PENDIENTE.value, nullable=False)
    lote_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    lote_aprobado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enviado_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def destinatario(self):
        return decrypt(self._destinatario, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    @destinatario.setter
    def destinatario(self, value):
        self._destinatario = encrypt(value, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    __table_args__ = (
        Index("ix_comunicaciones_tenant_lote", "tenant_id", "lote_id"),
        Index("ix_comunicaciones_tenant_estado", "tenant_id", "estado"),
    )
