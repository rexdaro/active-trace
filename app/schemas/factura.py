from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class FacturaCreate(BaseModel):
    usuario_id: uuid.UUID
    periodo: str
    detalle: str
    fecha: date
    monto: Decimal
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = None

    model_config = ConfigDict(extra="forbid")


class FacturaResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    usuario_id: uuid.UUID
    periodo: str
    detalle: str
    fecha: date
    monto: Decimal
    referencia_archivo: str | None
    tamano_kb: Decimal | None
    estado: str
    abonada_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
