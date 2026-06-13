from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    user_id: str | None
    resource: str | None
    status: str | None
    actor_id: str | None
    materia_id: str | None
    detalle: dict | None
    filas_afectadas: int | None
    ip: str | None
    user_agent: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricasResponse(BaseModel):
    acciones_por_dia: list[dict]
    comunicaciones_por_docente: list[dict]
    ultimas_acciones: list[AuditLogResponse]


class AuditoriaLogParams(BaseModel):
    fecha_desde: datetime | None = None
    fecha_hasta: datetime | None = None
    materia_id: uuid.UUID | None = None
    usuario_id: uuid.UUID | None = None
    accion: str | None = None
    estado: str | None = None
    offset: int = 0
    limit: int = 100
