import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.programa_materia import (
    ProgramaMateriaCreate,
    ProgramaMateriaUpdate,
    ProgramaMateriaRead,
    ProgramaMateriaListParams,
)
from app.services.programas_materia import ProgramaMateriaService

router = APIRouter(prefix="/api/v1/programas", tags=["Programas"])


@router.post(
    "",
    response_model=ProgramaMateriaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def create_programa(
    body: ProgramaMateriaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await ProgramaMateriaService.create(db, body, user)


@router.get(
    "",
    response_model=list[ProgramaMateriaRead],
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def list_programas(
    materia_id: uuid.UUID | None = Query(None),
    carrera_id: uuid.UUID | None = Query(None),
    cohorte_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    params = ProgramaMateriaListParams(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )
    items, total = await ProgramaMateriaService.list(db, user, params, offset=offset, limit=limit)
    return items


@router.get(
    "/{programa_id}",
    response_model=ProgramaMateriaRead,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def get_programa(
    programa_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await ProgramaMateriaService.get(db, programa_id, user)


@router.put(
    "/{programa_id}",
    response_model=ProgramaMateriaRead,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def update_programa(
    programa_id: uuid.UUID,
    body: ProgramaMateriaUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await ProgramaMateriaService.update(db, programa_id, body, user)


@router.delete(
    "/{programa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def delete_programa(
    programa_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    await ProgramaMateriaService.delete(db, programa_id, user)
