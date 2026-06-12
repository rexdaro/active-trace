import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.coloquio import (
    EvaluacionCreate,
    EvaluacionRead,
    ReservaCreate,
    ReservaRead,
    ReservaCancelResponse,
    ResultadoCreate,
    ResultadoRead,
    ImportAlumnosRequest,
    ImportAlumnosResponse,
    ConvocatoriaListResponse,
    PanelMetricas,
)
from app.services.coloquios import ColoquiosService

router = APIRouter(prefix="/api/v1/coloquios", tags=["coloquios"])


@router.post(
    "/convocatorias",
    response_model=EvaluacionRead,
    dependencies=[Depends(check_permission("coloquios:gestionar"))],
)
async def crear_convocatoria(
    request: EvaluacionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:gestionar")),
):
    return await ColoquiosService.crear_convocatoria(db, request, user)


@router.post(
    "/convocatorias/importar",
    response_model=ImportAlumnosResponse,
    dependencies=[Depends(check_permission("coloquios:gestionar"))],
)
async def import_alumnos(
    request: ImportAlumnosRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:gestionar")),
):
    return await ColoquiosService.import_alumnos(db, request, user)


@router.get(
    "/convocatorias",
    response_model=ConvocatoriaListResponse,
    dependencies=[Depends(check_permission("coloquios:ver"))],
)
async def get_convocatorias(
    materia_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:ver")),
):
    return await ColoquiosService.get_convocatorias(
        db, user, materia_id=materia_id, offset=offset, limit=limit,
    )


@router.get(
    "/metricas",
    response_model=PanelMetricas,
    dependencies=[Depends(check_permission("coloquios:ver"))],
)
async def get_metricas(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:ver")),
):
    return await ColoquiosService.get_panel_metricas(db, user)


@router.post(
    "/reservas",
    response_model=ReservaRead,
    dependencies=[Depends(check_permission("coloquios:reservar"))],
)
async def reservar_turno(
    request: ReservaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:reservar")),
):
    return await ColoquiosService.reservar_turno(db, request, user)


@router.post(
    "/reservas/{reserva_id}/cancelar",
    response_model=ReservaCancelResponse,
    dependencies=[Depends(check_permission("coloquios:reservar"))],
)
async def cancelar_reserva(
    reserva_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:reservar")),
):
    return await ColoquiosService.cancelar_reserva(db, reserva_id, user)


@router.get(
    "/mis-reservas",
    response_model=list[ReservaRead],
    dependencies=[Depends(check_permission("coloquios:reservar"))],
)
async def get_mis_reservas(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:reservar")),
):
    return await ColoquiosService.get_mis_reservas(db, user)


@router.post(
    "/resultados",
    response_model=ResultadoRead,
    dependencies=[Depends(check_permission("coloquios:gestionar"))],
)
async def registrar_resultado(
    request: ResultadoCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:gestionar")),
):
    return await ColoquiosService.registrar_resultado(db, request, user)


@router.get(
    "/convocatorias/{evaluacion_id}/resultados",
    response_model=list[ResultadoRead],
    dependencies=[Depends(check_permission("coloquios:ver"))],
)
async def get_resultados(
    evaluacion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:ver")),
):
    return await ColoquiosService.get_resultados(db, evaluacion_id, user)
