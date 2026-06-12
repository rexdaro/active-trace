from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.tarea import EstadoTarea


class TareaCreate(BaseModel):
    materia_id: uuid.UUID | None = None
    asignado_a: uuid.UUID
    descripcion: str
    contexto_id: uuid.UUID | None = None


class TareaUpdate(BaseModel):
    materia_id: uuid.UUID | None = None
    asignado_a: uuid.UUID | None = None
    descripcion: str | None = None
    estado: EstadoTarea | None = None
    contexto_id: uuid.UUID | None = None


class TareaEstadoUpdate(BaseModel):
    estado: EstadoTarea


class TareaResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID | None
    asignado_a: uuid.UUID
    asignado_por: uuid.UUID
    estado: str
    descripcion: str
    contexto_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TareaListParams(BaseModel):
    estado: str | None = None
    asignado_a: uuid.UUID | None = None
    materia_id: uuid.UUID | None = None
    search: str | None = None


class ComentarioTareaCreate(BaseModel):
    texto: str


class ComentarioTareaResponse(BaseModel):
    id: uuid.UUID
    tarea_id: uuid.UUID
    autor_id: uuid.UUID
    texto: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
