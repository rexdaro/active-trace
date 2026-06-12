import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PreviewRequest(BaseModel):
    destinatarios: list[uuid.UUID]
    asunto: str
    cuerpo: str
    materia_id: uuid.UUID


class PreviewItem(BaseModel):
    entrada_padron_id: uuid.UUID
    destinatario: str
    nombre: str
    asunto_renderizado: str
    cuerpo_renderizado: str


class PreviewResponse(BaseModel):
    preview_token: str
    items: list[PreviewItem]
    total: int
    errores: list[str]


class ConfirmRequest(BaseModel):
    preview_token: str


class ConfirmResponse(BaseModel):
    lote_id: uuid.UUID
    cantidad: int
    requiere_aprobacion: bool


class LoteSummary(BaseModel):
    lote_id: uuid.UUID
    enviado_por: uuid.UUID
    materia_id: uuid.UUID
    total: int
    pendientes: int
    enviando: int
    enviados: int
    errores: int
    cancelados: int
    created_at: datetime


class LoteListResponse(BaseModel):
    lotes: list[LoteSummary]
    total: int


class ComunicacionRead(BaseModel):
    id: uuid.UUID
    destinatario: str
    asunto: str
    cuerpo: str
    estado: str
    lote_id: uuid.UUID | None
    lote_aprobado: bool
    enviado_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoteDetailResponse(BaseModel):
    lote: LoteSummary
    comunicaciones: list[ComunicacionRead]


class AprobarLoteResponse(BaseModel):
    lote_id: uuid.UUID
    transicionados: int


class AprobarIndividualResponse(BaseModel):
    id: uuid.UUID
    estado: str


class RechazarLoteResponse(BaseModel):
    lote_id: uuid.UUID
    cancelados: int


class CancelarResponse(BaseModel):
    id: uuid.UUID
    estado: str


class EstadoPanelItem(BaseModel):
    materia_id: uuid.UUID
    materia_nombre: str
    pendientes: int
    enviando: int
    enviados: int
    errores: int
    cancelados: int


class EstadosPanelResponse(BaseModel):
    items: list[EstadoPanelItem]
