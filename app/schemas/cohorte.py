from pydantic import BaseModel, ConfigDict
import uuid
from typing import Optional

class CohorteBase(BaseModel):
    name: str
    carrera_id: uuid.UUID

class CohorteCreate(CohorteBase):
    pass

class CohorteRead(CohorteBase):
    id: uuid.UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
