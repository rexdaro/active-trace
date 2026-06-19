from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.usuario import UserCreate, UserRead
import bcrypt

router = APIRouter(prefix="/api/admin/usuarios", tags=["admin"])


@router.post("/", response_model=UserRead, dependencies=[Depends(check_permission("usuarios:gestionar"))])
async def create_usuario(
    usuario: UserCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("usuarios:gestionar")),
):
    existing = await db.execute(select(User).where(User.email == usuario.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    hashed = bcrypt.hashpw(usuario.password.encode("utf-8"), bcrypt.gensalt()).decode()
    new_user = User(
        tenant_id=user.tenant_id,
        email=usuario.email,
        hashed_password=hashed,
        dni=usuario.dni,
        cuil=usuario.cuil,
        cbu=usuario.cbu,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
