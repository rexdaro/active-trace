from __future__ import annotations
import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, field_validator


class SlotEncuentroCreate(BaseModel):
    materia_id: uuid.UUID
    dia_semana: str
    horario: str
    titulo: str
    meet_url: str | None = None
    fecha_inicio: date
    cant_semanas: int


class SlotEncuentroRead(BaseModel):
    id: uuid.UUID
    materia_id: uuid.UUID
    creado_por: uuid.UUID
    dia_semana: str
    horario: str
    titulo: str
    meet_url: str | None
    fecha_inicio: date
    cant_semanas: int
    activo: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstanciaEncuentroCreate(BaseModel):
    materia_id: uuid.UUID
    fecha: date
    hora: str
    titulo: str
    meet_url: str | None = None


class InstanciaEncuentroUpdate(BaseModel):
    estado: str | None = None
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None


class InstanciaEncuentroRead(BaseModel):
    id: uuid.UUID
    slot_id: uuid.UUID | None
    materia_id: uuid.UUID
    fecha: date
    hora: str
    titulo: str
    estado: str
    meet_url: str | None
    video_url: str | None
    comentario: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecurrenteRequest(BaseModel):
    materia_id: uuid.UUID
    dia_semana: str
    horario: str
    titulo: str
    meet_url: str | None = None
    fecha_inicio: date
    cant_semanas: int

    @field_validator("cant_semanas")
    @classmethod
    def cant_semanas_must_be_at_least_1(cls, v: int) -> int:
        if v < 1:
            raise ValueError("cant_semanas must be >= 1")
        return v


class RecurrenteResponse(BaseModel):
    slot: SlotEncuentroRead
    instancias_count: int


class HTMLBlockResponse(BaseModel):
    html: str


class InstanciasListResponse(BaseModel):
    items: list[InstanciaEncuentroRead]
    total: int


class GuardiaCreate(BaseModel):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: str
    horario: str
    comentarios: str | None = None


class GuardiaUpdate(BaseModel):
    estado: str | None = None
    comentarios: str | None = None


class GuardiaRead(BaseModel):
    id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: str
    horario: str
    estado: str
    comentarios: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuardiaListResponse(BaseModel):
    items: list[GuardiaRead]
    total: int
