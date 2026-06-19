import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime
from app.models.base import Base, TimestampMixin, TenantMixin

class Asignacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "asignaciones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    contexto_id: Mapped[uuid.UUID] = mapped_column(nullable=False) # Carrera/Materia/ etc.
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    desde: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hasta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    responsable = relationship("User", foreign_keys=[responsable_id])
