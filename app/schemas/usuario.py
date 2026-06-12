from pydantic import BaseModel, EmailStr
import uuid
from typing import Optional

class UsuarioBase(BaseModel):
    email: EmailStr
    dni: str
    cuil: str
    cbu: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioRead(UsuarioBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
