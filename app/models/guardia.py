import uuid
import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from app.models.base import Base, TimestampMixin, TenantMixin


class EstadoGuardia(str, enum.Enum):
    PENDIENTE = "Pendiente"
    REALIZADA = "Realizada"
    CANCELADA = "Cancelada"


class Guardia(Base, TimestampMixin, TenantMixin):
    __tablename__ = "guardias"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    asignacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asignaciones.id"), nullable=False)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    carrera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carreras.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohortes.id"), nullable=False)
    dia: Mapped[str] = mapped_column(String, nullable=False)
    horario: Mapped[str] = mapped_column(String, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, default=EstadoGuardia.PENDIENTE.value)
    comentarios: Mapped[str | None] = mapped_column(String, nullable=True)
