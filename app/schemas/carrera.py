from pydantic import BaseModel, ConfigDict
import uuid
from typing import Optional

class CarreraBase(BaseModel):
    name: str
    code: str

class CarreraCreate(CarreraBase):
    pass

class CarreraUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None

class CarreraRead(CarreraBase):
    id: uuid.UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
