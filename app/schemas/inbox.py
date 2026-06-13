from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MensajeSend(BaseModel):
    destinatario_id: uuid.UUID
    asunto: str
    cuerpo: str

    model_config = ConfigDict(extra='forbid')


class MensajeResponder(BaseModel):
    cuerpo: str

    model_config = ConfigDict(extra='forbid')


class MensajeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    remitente_id: uuid.UUID
    destinatario_id: uuid.UUID
    asunto: str
    cuerpo: str
    leido: bool
    hilo_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
