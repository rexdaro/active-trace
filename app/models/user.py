import uuid
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import Base, TimestampMixin, TenantMixin
from app.models.token import RefreshToken
from app.models.user_role import UserRole
import os
from app.core.security import encrypt, decrypt

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "dev-key")


class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String, nullable=True)

    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String, nullable=True)

    _dni: Mapped[str | None] = mapped_column("dni", String, nullable=True)
    _cuil: Mapped[str | None] = mapped_column("cuil", String, nullable=True)
    _cbu: Mapped[str | None] = mapped_column("cbu", String, nullable=True)

    nombre: Mapped[str | None] = mapped_column(String, nullable=True)
    datos_fiscales: Mapped[str | None] = mapped_column(String, nullable=True)
    datos_bancarios: Mapped[str | None] = mapped_column(String, nullable=True)
    regional: Mapped[str | None] = mapped_column(String, nullable=True)
    modalidad_cobro: Mapped[str | None] = mapped_column(String, nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(back_populates="user")

    # --- PII encryption for dni, cuil, cbu ---

    @hybrid_property
    def dni(self):
        raw = self._dni
        if raw is None:
            return None
        if not isinstance(raw, str):
            return raw
        return decrypt(raw, ENCRYPTION_KEY)

    @dni.setter
    def dni(self, value):
        if value is None:
            self._dni = None
        else:
            self._dni = encrypt(value, ENCRYPTION_KEY)

    @hybrid_property
    def cuil(self):
        raw = self._cuil
        if raw is None:
            return None
        if not isinstance(raw, str):
            return raw
        return decrypt(raw, ENCRYPTION_KEY)

    @cuil.setter
    def cuil(self, value):
        if value is None:
            self._cuil = None
        else:
            self._cuil = encrypt(value, ENCRYPTION_KEY)

    @hybrid_property
    def cbu(self):
        raw = self._cbu
        if raw is None:
            return None
        if not isinstance(raw, str):
            return raw
        return decrypt(raw, ENCRYPTION_KEY)

    @cbu.setter
    def cbu(self, value):
        if value is None:
            self._cbu = None
        else:
            self._cbu = encrypt(value, ENCRYPTION_KEY)


    def __init__(self, **kwargs):
        kwargs.pop("_email", None)
        super().__init__(**kwargs)


# Backward-compatible alias so existing imports still resolve
Usuario = User
