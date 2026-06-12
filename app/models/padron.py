import uuid
import os
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Boolean
from app.models.base import Base, TimestampMixin, TenantMixin
from app.core.security import encrypt, decrypt


class VersionPadron(Base, TimestampMixin, TenantMixin):
    __tablename__ = "versiones_padron"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materias.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohortes.id"), nullable=False)
    archivo_nombre: Mapped[str] = mapped_column(String, nullable=False)
    archivo_hash: Mapped[str] = mapped_column(String, nullable=False)
    origen: Mapped[str] = mapped_column(String, nullable=False)
    cargado_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EntradaPadron(Base, TimestampMixin, TenantMixin):
    __tablename__ = "entradas_padron"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("versiones_padron.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    apellidos: Mapped[str] = mapped_column(String, nullable=False)
    _email: Mapped[str] = mapped_column("email", String, nullable=False)
    comision: Mapped[str | None] = mapped_column(String, nullable=True)
    regional: Mapped[str | None] = mapped_column(String, nullable=True)

    @property
    def email(self):
        return decrypt(self._email, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    @email.setter
    def email(self, value):
        self._email = encrypt(value, os.environ.get("ENCRYPTION_KEY", "dev-key"))
