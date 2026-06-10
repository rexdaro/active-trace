from pydantic import BaseModel
import uuid
from datetime import datetime

class AsignacionBase(BaseModel):
    user_id: uuid.UUID
    role_id: uuid.UUID
    contexto_id: uuid.UUID
    responsable_id: uuid.UUID | None = None
    desde: datetime
    hasta: datetime | None = None

class AsignacionCreate(AsignacionBase):
    pass

class AsignacionRead(AsignacionBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
