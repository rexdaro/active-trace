from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from app.schemas.asignacion import AsignacionCreate, AsignacionRead


class AsignacionReadWithAttributes(AsignacionRead):
    model_config = ConfigDict(from_attributes=True)


class AsignacionMasivaRequest(BaseModel):
    asignaciones: list[AsignacionCreate]


class AsignacionMasivaResponse(BaseModel):
    creadas: int
    asignaciones: list[AsignacionReadWithAttributes]


class ClonarRequest(BaseModel):
    origen_contexto_id: uuid.UUID
    destino_contexto_id: uuid.UUID
    nuevo_desde: datetime
    nuevo_hasta: datetime | None = None


class ClonarResponse(BaseModel):
    clonadas: int
    asignaciones: list[AsignacionReadWithAttributes]


class ModificarVigenciaRequest(BaseModel):
    contexto_id: uuid.UUID
    nuevo_desde: datetime
    nuevo_hasta: datetime | None = None


class ModificarVigenciaResponse(BaseModel):
    modificadas: int
