from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.aviso import AlcanceAviso, SeveridadAviso


class AvisoCreate(BaseModel):
    titulo: str
    cuerpo: str
    alcance: AlcanceAviso
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso = SeveridadAviso.INFO
    inicio_en: datetime
    fin_en: datetime
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdate(BaseModel):
    titulo: str | None = None
    cuerpo: str | None = None
    alcance: AlcanceAviso | None = None
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    titulo: str
    cuerpo: str
    alcance: str
    materia_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    rol_destino: str | None
    severidad: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AcknowledgmentCreate(BaseModel):
    aviso_id: uuid.UUID


class AcknowledgmentResponse(BaseModel):
    id: uuid.UUID
    aviso_id: uuid.UUID
    usuario_id: uuid.UUID
    confirmado_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvisoConAckResponse(AvisoResponse):
    acknowledged: bool | None = None


class AvisoListParams(BaseModel):
    alcance: str | None = None
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: str | None = None
    activo: bool | None = None
    incluir_vencidos: bool = False
