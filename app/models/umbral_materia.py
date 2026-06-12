import uuid
from sqlalchemy import String, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class UmbralMateria(Base, TimestampMixin, TenantMixin):
    __tablename__ = "umbrales_materia"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asignaciones.id", ondelete="CASCADE"), nullable=False
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    umbral_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    valores_aprobatorios: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "asignacion_id", "materia_id",
            name="uix_umbral_asignacion_materia",
        ),
    )
