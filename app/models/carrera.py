import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UniqueConstraint
from typing import List, TYPE_CHECKING
from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.cohorte import Cohorte

class Carrera(Base, TimestampMixin, TenantMixin):
    __tablename__ = "carreras"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uix_carrera_tenant_code'),
    )

    cohortes: Mapped[List["Cohorte"]] = relationship(back_populates="carrera")
