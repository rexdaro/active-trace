from __future__ import annotations
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class AlcanceAviso(str, enum.Enum):
    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"


class SeveridadAviso(str, enum.Enum):
    INFO = "Info"
    ADVERTENCIA = "Advertencia"
    CRITICO = "Crítico"


class Aviso(Base, TimestampMixin, TenantMixin):
    __tablename__ = "avisos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alcance: Mapped[str] = mapped_column(String, nullable=False)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("materias.id"), nullable=True)
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cohortes.id"), nullable=True)
    rol_destino: Mapped[str | None] = mapped_column(String, nullable=True)
    severidad: Mapped[str] = mapped_column(String, nullable=False, default=SeveridadAviso.INFO.value)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fin_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AcknowledgmentAviso(Base, TimestampMixin, TenantMixin):
    __tablename__ = "acknowledgments_aviso"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    aviso_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("avisos.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "aviso_id", "usuario_id", name="uix_ack_aviso_usuario"),
    )
