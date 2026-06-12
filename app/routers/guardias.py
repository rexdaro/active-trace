import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.encuentro import (
    GuardiaCreate,
    GuardiaRead,
    GuardiaListResponse,
    GuardiaUpdate,
)
from app.services.encuentros import GuardiasService

router = APIRouter(prefix="/api/v1/guardias", tags=["guardias"])


@router.post(
    "/",
    response_model=GuardiaRead,
    dependencies=[Depends(check_permission("guardias:registrar"))],
)
async def registrar_guardia(
    request: GuardiaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("guardias:registrar")),
):
    return await GuardiasService.registrar(db, request, user)


@router.get(
    "/",
    response_model=GuardiaListResponse,
    dependencies=[Depends(check_permission("guardias:ver"))],
)
async def listar_guardias(
    materia_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("guardias:ver")),
):
    return await GuardiasService.listar(db, user, materia_id=materia_id, offset=offset, limit=limit)


@router.put(
    "/{guardia_id}",
    response_model=GuardiaRead,
    dependencies=[Depends(check_permission("guardias:registrar"))],
)
async def actualizar_guardia(
    guardia_id: uuid.UUID,
    request: GuardiaUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("guardias:registrar")),
):
    return await GuardiasService.actualizar(db, guardia_id, request, user)


@router.get(
    "/export",
    dependencies=[Depends(check_permission("guardias:ver"))],
)
async def exportar_guardias_csv(
    materia_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("guardias:ver")),
):
    from fastapi.responses import PlainTextResponse
    csv_content = await GuardiasService.exportar_csv(db, user, materia_id=materia_id)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=guardias.csv"},
    )
