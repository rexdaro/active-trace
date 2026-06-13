import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.fecha_academica import (
    FechaAcademicaCreate,
    FechaAcademicaUpdate,
    FechaAcademicaRead,
    FechaAcademicaListParams,
)
from app.services.fechas_academicas import FechaAcademicaService

router = APIRouter(prefix="/api/v1/fechas-academicas", tags=["Fechas Académicas"])


@router.post(
    "",
    response_model=FechaAcademicaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def create_fecha(
    body: FechaAcademicaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await FechaAcademicaService.create(db, body, user)


@router.get(
    "",
    response_model=list[FechaAcademicaRead],
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def list_fechas(
    materia_id: uuid.UUID | None = Query(None),
    cohorte_id: uuid.UUID | None = Query(None),
    tipo: str | None = Query(None),
    periodo: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    params = FechaAcademicaListParams(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo=tipo,
        periodo=periodo,
    )
    items, total = await FechaAcademicaService.list(db, user, params, offset=offset, limit=limit)
    return items


@router.get(
    "/{fecha_id}",
    response_model=FechaAcademicaRead,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def get_fecha(
    fecha_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await FechaAcademicaService.get(db, fecha_id, user)


@router.put(
    "/{fecha_id}",
    response_model=FechaAcademicaRead,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def update_fecha(
    fecha_id: uuid.UUID,
    body: FechaAcademicaUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await FechaAcademicaService.update(db, fecha_id, body, user)


@router.delete(
    "/{fecha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def delete_fecha(
    fecha_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    await FechaAcademicaService.delete(db, fecha_id, user)


@router.get(
    "/{fecha_id}/html",
    response_class=HTMLResponse,
    dependencies=[Depends(check_permission("estructura:gestionar"))],
)
async def get_fecha_html(
    fecha_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar")),
):
    return await FechaAcademicaService.generate_html(db, fecha_id, user)
