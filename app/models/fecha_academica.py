import uuid
import enum
from datetime import date as date_type
from sqlalchemy import String, Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class TipoFecha(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class FechaAcademica(Base, TimestampMixin, TenantMixin):
    __tablename__ = "fecha_academica"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohortes.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String, nullable=False)
    fecha: Mapped[date_type] = mapped_column(Date, nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
