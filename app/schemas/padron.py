from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime


class PadronEntry(BaseModel):
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None


class PadronPreviewResponse(BaseModel):
    preview_token: str
    columnas_detectadas: list[str]
    filas_count: int
    errores: list[str]


class PadronConfirmRequest(BaseModel):
    preview_token: str


class PadronConfirmResponse(BaseModel):
    version_id: uuid.UUID
    entradas_count: int


class VersionPadronRead(BaseModel):
    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    archivo_nombre: str
    archivo_hash: str
    origen: str
    cargado_por: uuid.UUID
    activa: bool
    created_at: datetime | None = None
    entradas_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class EntradaPadronRead(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    usuario_id: uuid.UUID | None
    nombre: str
    apellidos: str
    email: str
    comision: str | None
    regional: str | None

    model_config = ConfigDict(from_attributes=True)


class VaciarResponse(BaseModel):
    eliminadas: int


class SyncRequest(BaseModel):
    materia_id: uuid.UUID | None = None


class SyncResponse(BaseModel):
    status: str
    materias_procesadas: int
    errores: list[str]
