from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.analisis import (
    AtrasadosResponse,
    RankingResponse,
    ReporteMateria,
    EstadoSinDatos,
    NotasFinalesResponse,
    MonitorGeneralResponse,
    SeguimientoResponse,
)
from app.services.analisis import AnalisisService
import uuid

router = APIRouter(prefix="/api/v1/analisis", tags=["analisis"])


@router.get(
    "/materias/{materia_id}/atrasados",
    response_model=AtrasadosResponse,
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def get_atrasados(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.get_atrasados(db, materia_id, user)


@router.get(
    "/materias/{materia_id}/ranking",
    response_model=RankingResponse,
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def get_ranking(
    materia_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.get_ranking(db, materia_id, user, limit=limit, offset=offset)


@router.get(
    "/materias/{materia_id}/reporte",
    response_model=ReporteMateria | EstadoSinDatos,
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def get_reporte(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.get_reporte(db, materia_id, user)


@router.get(
    "/materias/{materia_id}/notas-finales",
    response_model=NotasFinalesResponse,
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def get_notas_finales(
    materia_id: uuid.UUID,
    ordenar_por: str = Query("promedio", pattern="^(promedio|apellidos)$"),
    orden: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.get_notas_finales(db, materia_id, user, ordenar_por=ordenar_por, orden=orden)


@router.get(
    "/materias/{materia_id}/tps-sin-corregir",
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def export_tps_sin_corregir(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.export_tps_sin_corregir(db, materia_id, user)


@router.get(
    "/monitor/general",
    response_model=MonitorGeneralResponse,
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def get_monitor_general(
    materia_id: uuid.UUID | None = Query(None),
    regional: str | None = Query(None),
    comision: str | None = Query(None),
    q: str | None = Query(None),
    estado_actividad: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.get_monitor_general(
        db, user,
        materia_id=materia_id,
        regional=regional,
        comision=comision,
        q=q,
        estado_actividad=estado_actividad,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/monitor/seguimiento",
    response_model=SeguimientoResponse,
    dependencies=[Depends(check_permission("atrasados:ver"))],
)
async def get_monitor_seguimiento(
    alumno_id: uuid.UUID | None = Query(None),
    email: str | None = Query(None),
    comision: str | None = Query(None),
    regional: str | None = Query(None),
    actividad: str | None = Query(None),
    min_cumplimiento_pct: int = Query(0, ge=0, le=100),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("atrasados:ver")),
):
    return await AnalisisService.get_monitor_seguimiento(
        db, user,
        alumno_id=alumno_id,
        email=email,
        comision=comision,
        regional=regional,
        actividad=actividad,
        min_cumplimiento_pct=min_cumplimiento_pct,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        offset=offset,
        limit=limit,
    )
