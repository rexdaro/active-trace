import uuid
from datetime import datetime
import enum
from sqlalchemy import String, Boolean, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class CalificacionOrigen(str, enum.Enum):
    IMPORTADO = "Importado"
    MANUAL = "Manual"


class Calificacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "calificaciones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entrada_padron_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entradas_padron.id", ondelete="RESTRICT"), nullable=False
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    actividad: Mapped[str] = mapped_column(String, nullable=False)
    nota_numerica: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    nota_textual: Mapped[str | None] = mapped_column(String, nullable=True)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origen: Mapped[str] = mapped_column(String, nullable=False)
    importado_por: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    importado_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "entrada_padron_id", "actividad", "materia_id",
            name="uix_calif_entrada_actividad",
        ),
    )
