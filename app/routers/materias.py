from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rbac import check_permission, get_current_user
from app.schemas.materia import MateriaCreate, MateriaRead
from app.models.materia import Materia
from app.models.user import User
from app.repositories.materia import MateriaRepository
import uuid

router = APIRouter(tags=["materias"])

@router.get("", response_model=list[MateriaRead])
async def get_materias(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = MateriaRepository(db)
    return await repo.get_all(user.tenant_id)

@router.post("", response_model=MateriaRead, dependencies=[Depends(check_permission("estructura:gestionar"))])
async def create_materia(
    materia_in: MateriaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar"))
):
    materia = Materia(
        **materia_in.model_dump(),
        tenant_id=user.tenant_id
    )
    repo = MateriaRepository(db)
    return await repo.create(materia)


@router.put("/{materia_id}", dependencies=[Depends(check_permission("estructura:gestionar"))])
async def update_materia(
    materia_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    repo = MateriaRepository(db)
    result = await db.execute(select(Materia).where(Materia.id == materia_id))
    materia = result.scalar_one_or_none()
    if not materia:
        raise HTTPException(status_code=404, detail="Materia not found")
    for campo in ["name", "code"]:
        if campo in body:
            setattr(materia, campo, body[campo])
    await db.commit()
    return materia


@router.delete("/{materia_id}", dependencies=[Depends(check_permission("estructura:gestionar"))])
async def delete_materia(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Materia).where(Materia.id == materia_id))
    materia = result.scalar_one_or_none()
    if not materia:
        raise HTTPException(status_code=404, detail="Materia not found")
    await db.delete(materia)
    await db.commit()
    return {"ok": True, "mensaje": "Materia eliminada"}
