from pydantic import BaseModel, ConfigDict
import uuid
from typing import Optional

class MateriaBase(BaseModel):
    name: str
    code: str

class MateriaCreate(MateriaBase):
    pass

class MateriaRead(MateriaBase):
    id: uuid.UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
