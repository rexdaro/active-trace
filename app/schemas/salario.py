from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class SalarioBaseCreate(BaseModel):
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class SalarioBaseUpdate(BaseModel):
    rol: str | None = None
    monto: Decimal | None = None
    desde: date | None = None
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class SalarioBaseResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalarioPlusCreate(BaseModel):
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class SalarioPlusUpdate(BaseModel):
    grupo: str | None = None
    rol: str | None = None
    descripcion: str | None = None
    monto: Decimal | None = None
    desde: date | None = None
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class SalarioPlusResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
