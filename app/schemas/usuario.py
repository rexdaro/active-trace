from pydantic import BaseModel, EmailStr
import uuid

class UsuarioBase(BaseModel):
    email: EmailStr
    dni: str
    cuil: str
    cbu: str

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioRead(UsuarioBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
