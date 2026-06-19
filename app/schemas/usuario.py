from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    is_2fa_enabled: bool = False
    dni: Optional[str] = None
    cuil: Optional[str] = None
    cbu: Optional[str] = None
    nombre: Optional[str] = None
    datos_fiscales: Optional[str] = None
    datos_bancarios: Optional[str] = None
    regional: Optional[str] = None
    modalidad_cobro: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    dni: Optional[str] = None
    cuil: Optional[str] = None
    cbu: Optional[str] = None
    nombre: Optional[str] = None
    datos_fiscales: Optional[str] = None
    datos_bancarios: Optional[str] = None
    regional: Optional[str] = None
    modalidad_cobro: Optional[str] = None
    role_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)


# Backward-compat aliases so old imports still resolve
UsuarioBase = UserCreate
UsuarioCreate = UserCreate
UsuarioRead = UserRead
