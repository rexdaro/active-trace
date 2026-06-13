from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProgramaMateriaCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    titulo: str
    referencia_archivo: str | None = None


class ProgramaMateriaUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    titulo: str | None = None
    referencia_archivo: str | None = None


class ProgramaMateriaRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    titulo: str
    referencia_archivo: str | None
    cargado_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProgramaMateriaListParams(BaseModel):
    model_config = ConfigDict(extra='forbid')

    materia_id: uuid.UUID | None = None
    carrera_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
