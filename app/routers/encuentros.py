import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.encuentro import (
    RecurrenteRequest,
    RecurrenteResponse,
    InstanciaEncuentroCreate,
    InstanciaEncuentroUpdate,
    InstanciaEncuentroRead,
    HTMLBlockResponse,
    InstanciasListResponse,
)
from app.services.encuentros import EncuentrosService

router = APIRouter(prefix="/api/v1/encuentros", tags=["encuentros"])


@router.get(
    "",
    response_model=list[InstanciaEncuentroRead],
    dependencies=[Depends(check_permission("encuentros:ver"))],
)
async def get_all_encuentros(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:ver")),
):
    result = await EncuentrosService.get_all_instancias(db, user, offset=offset, limit=limit)
    return result.items


@router.post(
    "/recurrente",
    response_model=RecurrenteResponse,
    dependencies=[Depends(check_permission("encuentros:gestionar"))],
)
async def crear_recurrente(
    request: RecurrenteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:gestionar")),
):
    return await EncuentrosService.crear_recurrente(db, request, user)


@router.post(
    "/unico",
    response_model=InstanciaEncuentroRead,
    dependencies=[Depends(check_permission("encuentros:gestionar"))],
)
async def crear_unico(
    request: InstanciaEncuentroCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:gestionar")),
):
    return await EncuentrosService.crear_unico(db, request, user)


@router.put(
    "/instancias/{instancia_id}",
    response_model=InstanciaEncuentroRead,
    dependencies=[Depends(check_permission("encuentros:gestionar"))],
)
async def editar_instancia(
    instancia_id: uuid.UUID,
    request: InstanciaEncuentroUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:gestionar")),
):
    return await EncuentrosService.editar_instancia(db, instancia_id, request, user)


@router.get(
    "/materias/{materia_id}/instancias",
    response_model=InstanciasListResponse,
    dependencies=[Depends(check_permission("encuentros:gestionar"))],
)
async def list_instancias(
    materia_id: uuid.UUID,
    estado: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:gestionar")),
):
    return await EncuentrosService.get_instancias_by_materia(
        db, materia_id, user, estado=estado, offset=offset, limit=limit,
    )


@router.get(
    "/instancias",
    response_model=InstanciasListResponse,
    dependencies=[Depends(check_permission("encuentros:ver"))],
)
async def get_all_instancias(
    materia_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:ver")),
):
    return await EncuentrosService.get_all_instancias(
        db, user, materia_id=materia_id, offset=offset, limit=limit,
    )


@router.get(
    "/materias/{materia_id}/html",
    response_model=HTMLBlockResponse,
    dependencies=[Depends(check_permission("encuentros:gestionar"))],
)
async def generate_html_block(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("encuentros:gestionar")),
):
    return await EncuentrosService.generate_html_block(db, materia_id, user)
