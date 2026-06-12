import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.aviso import (
    AvisoCreate,
    AvisoUpdate,
    AvisoResponse,
    AvisoConAckResponse,
    AcknowledgmentResponse,
    AvisoListParams,
)
from app.services.avisos import AvisoService

router = APIRouter(prefix="/api/v1/avisos", tags=["Avisos"])


@router.post(
    "",
    response_model=AvisoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def create_aviso(
    body: AvisoCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    return await AvisoService.create(db, body, user)


@router.put(
    "/{aviso_id}",
    response_model=AvisoResponse,
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def update_aviso(
    aviso_id: uuid.UUID,
    body: AvisoUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    return await AvisoService.update(db, aviso_id, body, user)


@router.delete(
    "/{aviso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def delete_aviso(
    aviso_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    await AvisoService.delete(db, aviso_id, user)


@router.get(
    "/mis-avisos",
    response_model=list[AvisoConAckResponse],
    dependencies=[Depends(check_permission("avisos:ver"))],
)
async def list_mis_avisos(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:ver")),
):
    return await AvisoService.list_para_usuario(db, user)


@router.get(
    "/{aviso_id}",
    response_model=AvisoResponse,
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def get_aviso(
    aviso_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    return await AvisoService.get(db, aviso_id, user)


@router.post(
    "/{aviso_id}/confirmar-lectura",
    response_model=AcknowledgmentResponse,
    dependencies=[Depends(check_permission("avisos:confirmar"))],
)
async def confirmar_lectura(
    aviso_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:confirmar")),
):
    return await AvisoService.confirmar_lectura(db, aviso_id, user)


@router.get(
    "/{aviso_id}/metricas",
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def get_metricas(
    aviso_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    return await AvisoService.get_metricas(db, aviso_id, user)


@router.get(
    "",
    response_model=list[AvisoResponse],
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def list_all_avisos(
    alcance: str | None = Query(None),
    materia_id: uuid.UUID | None = Query(None),
    cohorte_id: uuid.UUID | None = Query(None),
    rol_destino: str | None = Query(None),
    severidad: str | None = Query(None),
    activo: bool | None = Query(None),
    incluir_vencidos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    params = AvisoListParams(
        alcance=alcance,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        rol_destino=rol_destino,
        severidad=severidad,
        activo=activo,
        incluir_vencidos=incluir_vencidos,
    )
    return await AvisoService.list_all(db, user, params)


@router.get(
    "/{aviso_id}/acks",
    response_model=list[AcknowledgmentResponse],
    dependencies=[Depends(check_permission("avisos:publicar"))],
)
async def list_acks(
    aviso_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("avisos:publicar")),
):
    return await AvisoService.list_acks(db, aviso_id, user)
