import uuid
import enum
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, Index
from app.models.base import Base, TimestampMixin, TenantMixin


class EstadoInstancia(str, enum.Enum):
    PROGRAMADO = "Programado"
    REALIZADO = "Realizado"
    CANCELADO = "Cancelado"


class SlotEncuentro(Base, TimestampMixin, TenantMixin):
    __tablename__ = "slots_encuentro"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    creado_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    dia_semana: Mapped[str] = mapped_column(String, nullable=False)
    horario: Mapped[str] = mapped_column(String, nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    meet_url: Mapped[str | None] = mapped_column(String, nullable=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    cant_semanas: Mapped[int] = mapped_column(Integer, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InstanciaEncuentro(Base, TimestampMixin, TenantMixin):
    __tablename__ = "instancias_encuentro"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("slots_encuentro.id", ondelete="SET NULL"), nullable=True)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[str] = mapped_column(String, nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, default=EstadoInstancia.PROGRAMADO.value)
    meet_url: Mapped[str | None] = mapped_column(String, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    comentario: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("ix_instancias_materia_fecha", "tenant_id", "materia_id", "fecha"),
    )
