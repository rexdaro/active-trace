from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission, get_current_user
from app.schemas.cohorte import CohorteCreate, CohorteRead
from app.models.cohorte import Cohorte
from app.models.user import User
from app.repositories.cohorte import CohorteRepository
import uuid
from typing import Optional

router = APIRouter(prefix="/api/cohortes", tags=["cohortes"])

@router.get("", response_model=list[CohorteRead])
async def get_cohortes(
    carrera_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = CohorteRepository(db)
    if carrera_id:
        from sqlalchemy import select
        query = select(Cohorte).where(Cohorte.tenant_id == user.tenant_id, Cohorte.carrera_id == carrera_id)
        result = await db.execute(query)
        return list(result.scalars().all())
    return await repo.get_all(user.tenant_id)

@router.post("", response_model=CohorteRead, dependencies=[Depends(check_permission("estructura:gestionar"))])
async def create_cohorte(
    cohorte_in: CohorteCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar"))
):
    cohorte = Cohorte(
        **cohorte_in.model_dump(),
        tenant_id=user.tenant_id
    )
    repo = CohorteRepository(db)
    return await repo.create(cohorte)


@router.put("/{cohorte_id}", dependencies=[Depends(check_permission("estructura:gestionar"))])
async def update_cohorte(
    cohorte_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(select(Cohorte).where(Cohorte.id == cohorte_id))
    cohorte = result.scalar_one_or_none()
    if not cohorte:
        raise HTTPException(status_code=404, detail="Cohorte not found")
    for campo in ["name", "carrera_id"]:
        if campo in body:
            setattr(cohorte, campo, body[campo])
    await db.commit()
    return cohorte


@router.delete("/{cohorte_id}", dependencies=[Depends(check_permission("estructura:gestionar"))])
async def delete_cohorte(
    cohorte_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(select(Cohorte).where(Cohorte.id == cohorte_id))
    cohorte = result.scalar_one_or_none()
    if not cohorte:
        raise HTTPException(status_code=404, detail="Cohorte not found")
    await db.delete(cohorte)
    await db.commit()
    return {"ok": True, "mensaje": "Cohorte eliminado"}
