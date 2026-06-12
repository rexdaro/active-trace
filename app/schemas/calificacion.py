import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ActividadDetectada(BaseModel):
    nombre: str
    tipo: str  # "numerica" | "textual"
    valores_muestra: list


class CalificacionPreviewResponse(BaseModel):
    preview_token: str
    actividades_detectadas: list[ActividadDetectada]
    alumnos_count: int
    errores: list[str]


class CalificacionConfirmRequest(BaseModel):
    preview_token: str
    actividades_seleccionadas: list[str]


class CalificacionConfirmResponse(BaseModel):
    calificaciones_count: int
    aprobados_count: int
    no_aprobados_count: int


class CalificacionRead(BaseModel):
    id: uuid.UUID
    entrada_padron_id: uuid.UUID
    materia_id: uuid.UUID
    actividad: str
    nota_numerica: Decimal | None = None
    nota_textual: str | None = None
    aprobado: bool
    origen: str
    importado_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CalificacionListResponse(BaseModel):
    calificaciones: list[CalificacionRead]
    total: int


class PosibleSinCorregir(BaseModel):
    alumno: str
    actividad: str
    fecha_entrega: str | None = None


class FinalizacionPreviewResponse(BaseModel):
    preview_token: str
    posibles_sin_corregir: list[PosibleSinCorregir]


class FinalizacionConfirmRequest(BaseModel):
    preview_token: str


class FinalizacionConfirmResponse(BaseModel):
    registros_detectados: int


class UmbralRead(BaseModel):
    umbral_pct: int
    valores_aprobatorios: list[str]
    es_defecto: bool = True

    model_config = ConfigDict(from_attributes=True)


class UmbralUpdateRequest(BaseModel):
    umbral_pct: int | None = None
    valores_aprobatorios: list[str] | None = None


class UmbralUpdateResponse(BaseModel):
    umbral_pct: int
    valores_aprobatorios: list[str]


class VaciarResponse(BaseModel):
    eliminados_count: int
