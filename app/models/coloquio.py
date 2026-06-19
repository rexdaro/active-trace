import uuid
import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class TipoEvaluacion(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class EstadoReserva(str, enum.Enum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"


class Evaluacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "evaluaciones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohortes.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    instancia: Mapped[str] = mapped_column(String, nullable=False)
    cupos_por_dia: Mapped[int] = mapped_column(Integer, nullable=False, default=10)


class ReservaEvaluacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "reservas_evaluacion"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    alumno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, default=EstadoReserva.ACTIVA.value)

    __table_args__ = (
        UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="uix_reserva_alumno_evaluacion"),
        Index("ix_reservas_fecha", "tenant_id", "evaluacion_id", "fecha_hora"),
    )


class ResultadoEvaluacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "resultados_evaluacion"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    alumno_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    nota_final: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="uix_resultado_alumno_evaluacion"),
    )
