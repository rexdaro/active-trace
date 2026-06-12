from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvaluacionCreate(BaseModel):
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    cupos_por_dia: int = 10


class EvaluacionRead(BaseModel):
    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    cupos_por_dia: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReservaCreate(BaseModel):
    evaluacion_id: uuid.UUID
    fecha_hora: datetime


class ReservaRead(BaseModel):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    fecha_hora: datetime
    estado: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReservaCancelResponse(BaseModel):
    id: uuid.UUID
    estado: str


class ResultadoCreate(BaseModel):
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    nota_final: str


class ResultadoRead(BaseModel):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    nota_final: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ImportAlumnosRequest(BaseModel):
    evaluacion_id: uuid.UUID
    alumno_ids: list[uuid.UUID]


class ImportAlumnosResponse(BaseModel):
    evaluacion_id: uuid.UUID
    cantidad: int


class ConvovatoriaListItem(BaseModel):
    id: uuid.UUID
    materia_id: uuid.UUID
    materia_nombre: str = ""
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    cupos_por_dia: int
    total_alumnos: int = 0
    reservas_activas: int = 0
    created_at: datetime


class ConvocatoriaListResponse(BaseModel):
    items: list[ConvovatoriaListItem]
    total: int


class PanelMetricas(BaseModel):
    total_evaluaciones: int
    total_reservas_activas: int
    total_resultados: int
    total_alumnos_convocados: int
