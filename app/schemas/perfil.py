from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PerfilRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    dni: str
    cuil: str
    cbu: str | None
    nombre: str | None
    datos_fiscales: str | None
    datos_bancarios: str | None
    regional: str | None
    modalidad_cobro: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PerfilUpdate(BaseModel):
    nombre: str | None = None
    datos_fiscales: str | None = None
    datos_bancarios: str | None = None
    regional: str | None = None
    modalidad_cobro: str | None = None
    cuil: str | None = None

    model_config = ConfigDict(extra='forbid')
