import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, UniqueConstraint
from app.models.base import Base, TimestampMixin, TenantMixin

class Materia(Base, TimestampMixin, TenantMixin):
    __tablename__ = "materias"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uix_materia_tenant_code'),
    )
