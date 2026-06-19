import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import get_current_user
from app.models.user import User
from app.schemas.perfil import PerfilRead, PerfilUpdate
from app.services.audit import AuditService

router = APIRouter(prefix="/api/v1/perfil", tags=["Perfil"])


@router.get("", response_model=PerfilRead)
async def get_perfil(
    user: User = Depends(get_current_user),
):
    return user


@router.put("", response_model=PerfilRead)
async def update_perfil(
    body: PerfilUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.cuil is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El CUIL no puede ser modificado",
        )

    update_data = body.model_dump(exclude_unset=True, exclude={"cuil"})
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    await AuditService.log_action(
        db=db,
        action="PERFIL_ACTUALIZAR",
        user_id=str(user.id),
        resource="perfil",
        status="success",
        actor_id=str(user.id),
        detalle={"fields": list(update_data.keys())},
    )

    return user
