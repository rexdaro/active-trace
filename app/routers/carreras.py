from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.schemas.carrera import CarreraCreate, CarreraRead, CarreraUpdate
from app.models.carrera import Carrera
from app.models.user import User
from app.repositories.carrera import CarreraRepository
import uuid

router = APIRouter(prefix="/api/carreras", tags=["carreras"])

@router.post("", response_model=CarreraRead, dependencies=[Depends(check_permission("estructura:gestionar"))])
async def create_carrera(
    carrera_in: CarreraCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar"))
):
    carrera = Carrera(
        **carrera_in.model_dump(),
        tenant_id=user.tenant_id
    )
    repo = CarreraRepository(db)
    return await repo.create(carrera)

@router.get("/{carrera_id}", response_model=CarreraRead, dependencies=[Depends(check_permission("estructura:gestionar"))])
async def get_carrera(carrera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = CarreraRepository(db)
    carrera = await repo.get(carrera_id)
    if not carrera:
        raise HTTPException(status_code=404, detail="Carrera not found")
    return carrera

@router.get("", response_model=list[CarreraRead], dependencies=[Depends(check_permission("estructura:gestionar"))])
async def get_carreras(db: AsyncSession = Depends(get_db), user: User = Depends(check_permission("estructura:gestionar"))):
    repo = CarreraRepository(db)
    return await repo.get_all(user.tenant_id)


@router.put("/{carrera_id}", dependencies=[Depends(check_permission("estructura:gestionar"))])
async def update_carrera(
    carrera_id: uuid.UUID,
    body: CarreraUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db)
    carrera = await repo.get(carrera_id)
    if not carrera:
        raise HTTPException(status_code=404, detail="Carrera not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(carrera, field, value)
    await db.commit()
    return carrera


@router.delete("/{carrera_id}", dependencies=[Depends(check_permission("estructura:gestionar"))])
async def delete_carrera(
    carrera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db)
    carrera = await repo.get(carrera_id)
    if not carrera:
        raise HTTPException(status_code=404, detail="Carrera not found")
    await db.delete(carrera)
    await db.commit()
    return {"ok": True, "mensaje": "Carrera eliminada"}

