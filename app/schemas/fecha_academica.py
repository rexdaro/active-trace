from __future__ import annotations
import uuid
from datetime import date as date_type, datetime
from pydantic import BaseModel, ConfigDict
from app.models.fecha_academica import TipoFecha


class FechaAcademicaCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: TipoFecha
    numero: int
    periodo: str
    fecha: date_type
    titulo: str


class FechaAcademicaUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    tipo: TipoFecha | None = None
    numero: int | None = None
    periodo: str | None = None
    fecha: date_type | None = None
    titulo: str | None = None


class FechaAcademicaRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    numero: int
    periodo: str
    fecha: date_type
    titulo: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FechaAcademicaListParams(BaseModel):
    model_config = ConfigDict(extra='forbid')

    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    tipo: str | None = None
    periodo: str | None = None
