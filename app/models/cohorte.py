import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UniqueConstraint
from typing import TYPE_CHECKING
from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.carrera import Carrera

class Cohorte(Base, TimestampMixin, TenantMixin):
    __tablename__ = "cohortes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    carrera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carreras.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    carrera: Mapped["Carrera"] = relationship(back_populates="cohortes")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'carrera_id', 'name', name='uix_cohorte_tenant_carrera_name'),
    )
