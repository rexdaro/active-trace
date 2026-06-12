from __future__ import annotations
import uuid
import enum
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class EstadoTarea(str, enum.Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"


class Tarea(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tareas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("materias.id"), nullable=True)
    asignado_a: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    asignado_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, default=EstadoTarea.PENDIENTE.value)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    contexto_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)


class ComentarioTarea(Base, TimestampMixin, TenantMixin):
    __tablename__ = "comentarios_tarea"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tarea_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tareas.id", ondelete="CASCADE"), nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
