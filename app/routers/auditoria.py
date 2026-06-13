import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.auditoria import MetricasResponse, AuditLogResponse, AuditoriaLogParams
from app.services.auditoria import AuditoriaService

router = APIRouter(prefix="/api/v1/auditoria", tags=["Auditoria"])


@router.get(
    "/metricas",
    response_model=MetricasResponse,
    dependencies=[Depends(check_permission("auditoria:ver"))],
)
async def get_metricas(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("auditoria:ver")),
):
    return await AuditoriaService.get_metricas(db, user)


@router.get(
    "/log",
    dependencies=[Depends(check_permission("auditoria:ver"))],
)
async def get_log(
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    materia_id: str | None = Query(None),
    usuario_id: str | None = Query(None),
    accion: str | None = Query(None),
    estado: str | None = Query(None),
    offset: int = Query(0),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("auditoria:ver")),
):
    params = AuditoriaLogParams(
        fecha_desde=datetime.fromisoformat(fecha_desde) if fecha_desde else None,
        fecha_hasta=datetime.fromisoformat(fecha_hasta) if fecha_hasta else None,
        materia_id=uuid.UUID(materia_id) if materia_id else None,
        usuario_id=uuid.UUID(usuario_id) if usuario_id else None,
        accion=accion if accion else None,
        estado=estado if estado else None,
        offset=offset,
        limit=limit,
    )
    items, total = await AuditoriaService.get_log(db, params, user)
    return {
        "items": [AuditLogResponse.model_validate(item) for item in items],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
