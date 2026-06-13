import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, TenantMixin


class ProgramaMateria(Base, TimestampMixin, TenantMixin):
    __tablename__ = "programa_materia"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    carrera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carreras.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohortes.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(String, nullable=True)
    cargado_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
