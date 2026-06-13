import uuid
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import Base, TimestampMixin, TenantMixin
from app.models.token import RefreshToken
from app.models.user_role import UserRole
import os
from app.core.security import encrypt, decrypt

class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_roles: Mapped[List["UserRole"]] = relationship(back_populates="user")

class Usuario(Base, TimestampMixin, TenantMixin):
    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint('tenant_id', 'email', name='uix_tenant_email'),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    _email: Mapped[str] = mapped_column("email", String, nullable=False)
    _dni: Mapped[str] = mapped_column("dni", String, nullable=False)
    _cuil: Mapped[str] = mapped_column("cuil", String, nullable=False)
    _cbu: Mapped[str | None] = mapped_column("cbu", String, nullable=True)

    @hybrid_property
    def email(self):
        raw = self._email
        if not isinstance(raw, str):
            return raw  # class-level access (e.g. hasattr during __init__)
        return decrypt(raw, os.environ.get("ENCRYPTION_KEY", "dev-key"))
    
    @email.setter
    def email(self, value):
        self._email = encrypt(value, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    @hybrid_property
    def dni(self):
        raw = self._dni
        if not isinstance(raw, str):
            return raw
        return decrypt(raw, os.environ.get("ENCRYPTION_KEY", "dev-key"))
    
    @dni.setter
    def dni(self, value):
        self._dni = encrypt(value, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    @hybrid_property
    def cuil(self):
        raw = self._cuil
        if not isinstance(raw, str):
            return raw
        return decrypt(raw, os.environ.get("ENCRYPTION_KEY", "dev-key"))
    
    @cuil.setter
    def cuil(self, value):
        self._cuil = encrypt(value, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    @hybrid_property
    def cbu(self):
        raw = self._cbu
        if raw is None:
            return None
        if not isinstance(raw, str):
            return raw
        return decrypt(raw, os.environ.get("ENCRYPTION_KEY", "dev-key"))
    
    @cbu.setter
    def cbu(self, value):
        if value is None:
            self._cbu = None
        else:
            self._cbu = encrypt(value, os.environ.get("ENCRYPTION_KEY", "dev-key"))

    # Perfil fields
    nombre: Mapped[str | None] = mapped_column(String, nullable=True)
    datos_fiscales: Mapped[str | None] = mapped_column(String, nullable=True)
    datos_bancarios: Mapped[str | None] = mapped_column(String, nullable=True)
    regional: Mapped[str | None] = mapped_column(String, nullable=True)
    modalidad_cobro: Mapped[str | None] = mapped_column(String, nullable=True)
