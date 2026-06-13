from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class LiquidacionCreate(BaseModel):
    cohorte_id: uuid.UUID
    periodo: str
    usuario_id: uuid.UUID
    rol: str
    comisiones: str | None = None
    monto_base: Decimal
    monto_plus: Decimal = Decimal("0")
    total: Decimal
    es_nexo: bool = False

    model_config = ConfigDict(extra="forbid")


class LiquidacionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    cohorte_id: uuid.UUID
    periodo: str
    usuario_id: uuid.UUID
    rol: str
    comisiones: str | None
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalcularLiquidacionRequest(BaseModel):
    periodo: str

    model_config = ConfigDict(extra="forbid")
