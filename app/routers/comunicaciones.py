import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.comunicacion import (
    PreviewRequest,
    PreviewResponse,
    ConfirmRequest,
    ConfirmResponse,
    LoteListResponse,
    LoteDetailResponse,
    AprobarLoteResponse,
    AprobarIndividualResponse,
    RechazarLoteResponse,
    CancelarResponse,
    EstadosPanelResponse,
)
from app.services.comunicaciones import ComunicacionesService

router = APIRouter(prefix="/api/v1/comunicaciones", tags=["comunicaciones"])


@router.post(
    "/preview",
    response_model=PreviewResponse,
    dependencies=[Depends(check_permission("comunicacion:enviar"))],
)
async def preview(
    request: PreviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:enviar")),
):
    return await ComunicacionesService.preview(db, request, user)


@router.post(
    "/confirm",
    response_model=ConfirmResponse,
    dependencies=[Depends(check_permission("comunicacion:enviar"))],
)
async def confirm(
    request: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:enviar")),
):
    return await ComunicacionesService.confirm(db, request, user)


@router.get(
    "/lotes",
    response_model=LoteListResponse,
    dependencies=[Depends(check_permission("comunicacion:enviar"))],
)
async def listar_lotes(
    materia_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:enviar")),
):
    return await ComunicacionesService.get_lotes(db, materia_id, user, offset, limit)


@router.get(
    "/lotes/{lote_id}",
    response_model=LoteDetailResponse,
    dependencies=[Depends(check_permission("comunicacion:enviar"))],
)
async def detalle_lote(
    lote_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:enviar")),
):
    return await ComunicacionesService.get_lote_detalle(db, lote_id, user)


@router.post(
    "/lotes/{lote_id}/aprobar",
    response_model=AprobarLoteResponse,
    dependencies=[Depends(check_permission("comunicacion:aprobar"))],
)
async def aprobar_lote(
    lote_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:aprobar")),
):
    return await ComunicacionesService.aprobar_lote(db, lote_id, user)


@router.post(
    "/{comunicacion_id}/aprobar",
    response_model=AprobarIndividualResponse,
    dependencies=[Depends(check_permission("comunicacion:aprobar"))],
)
async def aprobar_individual(
    comunicacion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:aprobar")),
):
    return await ComunicacionesService.aprobar_individual(db, comunicacion_id, user)


@router.post(
    "/lotes/{lote_id}/rechazar",
    response_model=RechazarLoteResponse,
    dependencies=[Depends(check_permission("comunicacion:aprobar"))],
)
async def rechazar_lote(
    lote_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:aprobar")),
):
    return await ComunicacionesService.rechazar_lote(db, lote_id, user)


@router.post(
    "/{comunicacion_id}/cancelar",
    response_model=CancelarResponse,
    dependencies=[Depends(check_permission("comunicacion:enviar"))],
)
async def cancelar_individual(
    comunicacion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:enviar")),
):
    return await ComunicacionesService.cancelar_individual(db, comunicacion_id, user)


@router.get(
    "/estados",
    response_model=EstadosPanelResponse,
    dependencies=[Depends(check_permission("comunicacion:enviar"))],
)
async def estados_panel(
    materia_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("comunicacion:enviar")),
):
    return await ComunicacionesService.get_estados_panel(db, materia_id, user)
