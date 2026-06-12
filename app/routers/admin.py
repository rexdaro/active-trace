from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead

router = APIRouter(prefix="/api/admin/usuarios", tags=["admin"])

@router.post("/", response_model=UsuarioRead, dependencies=[Depends(check_permission("usuarios:gestionar"))])
async def create_usuario(
    usuario: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("usuarios:gestionar"))
):
    new_usuario = Usuario(
        tenant_id=user.tenant_id,
        email=usuario.email,
        dni=usuario.dni,
        cuil=usuario.cuil,
        cbu=usuario.cbu
    )
    db.add(new_usuario)
    await db.commit()
    await db.refresh(new_usuario)
    return new_usuario
