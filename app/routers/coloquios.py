import uuid

from fastapi import APIRouter, Depends, Query, status
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


# ─── Static routes (these take priority over parameterized) ──────────────


@router.get(
    "",
    response_model=ConvocatoriaListResponse,
    dependencies=[Depends(check_permission("coloquios:ver"))],
)
async def get_coloquios(
    materia_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:ver")),
):
    return await ColoquiosService.get_convocatorias(
        db, user, materia_id=materia_id, offset=offset, limit=limit,
    )


@router.post(
    "",
    response_model=EvaluacionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("coloquios:gestionar"))],
)
async def crear_coloquio(
    request: EvaluacionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:gestionar")),
):
    return await ColoquiosService.crear_convocatoria(db, request, user)


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


# ─── Parameterized routes (must come AFTER static routes) ────────────────


@router.get(
    "/{evaluacion_id}/metricas",
    dependencies=[Depends(check_permission("coloquios:ver"))],
)
async def get_coloquio_metricas(
    evaluacion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:ver")),
):
    panel = await ColoquiosService.get_panel_metricas(db, user)
    return {
        "convocados": panel.total_alumnos_convocados,
        "reservas": panel.total_reservas_activas,
        "libres": max(0, panel.total_alumnos_convocados - panel.total_reservas_activas),
    }


@router.post(
    "/{evaluacion_id}/importar",
    response_model=ImportAlumnosResponse,
    dependencies=[Depends(check_permission("coloquios:gestionar"))],
)
async def importar_alumnos_a_coloquio(
    evaluacion_id: uuid.UUID,
    request: ImportAlumnosRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("coloquios:gestionar")),
):
    request.evaluacion_id = evaluacion_id
    return await ColoquiosService.import_alumnos(db, request, user)


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
