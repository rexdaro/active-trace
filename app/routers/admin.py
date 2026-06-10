from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead
import uuid

router = APIRouter(prefix="/api/admin/usuarios", tags=["admin"])

@router.post("/", response_model=UsuarioRead)
async def create_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    new_usuario = Usuario(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email=usuario.email,
        dni=usuario.dni,
        cuil=usuario.cuil,
        cbu=usuario.cbu
    )
    db.add(new_usuario)
    await db.commit()
    await db.refresh(new_usuario)
    return new_usuario
