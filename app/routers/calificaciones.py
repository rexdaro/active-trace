from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.calificacion import (
    CalificacionPreviewResponse,
    CalificacionConfirmRequest,
    CalificacionConfirmResponse,
    CalificacionListResponse,
    FinalizacionPreviewResponse,
    FinalizacionConfirmRequest,
    FinalizacionConfirmResponse,
    UmbralRead,
    UmbralUpdateRequest,
    UmbralUpdateResponse,
    VaciarResponse,
    CalificacionRead,
)
from app.services.calificaciones import CalificacionesService
from app.repositories.calificaciones import CalificacionesRepository
from app.repositories.umbral_materia import UmbralMateriaRepository
import uuid

router = APIRouter(prefix="/api/v1/materias", tags=["calificaciones"])


@router.post(
    "/{materia_id}/calificaciones/preview",
    response_model=CalificacionPreviewResponse,
    dependencies=[Depends(check_permission("calificaciones:importar"))],
)
async def preview_calificaciones(
    materia_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(check_permission("calificaciones:importar")),
):
    return await CalificacionesService.preview(materia_id, file)


@router.post(
    "/{materia_id}/calificaciones/confirm",
    response_model=CalificacionConfirmResponse,
    dependencies=[Depends(check_permission("calificaciones:importar"))],
)
async def confirm_calificaciones(
    materia_id: uuid.UUID,
    request: CalificacionConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:importar")),
):
    return await CalificacionesService.confirm(db, request.preview_token, user, request.actividades_seleccionadas)


@router.get(
    "/{materia_id}/calificaciones",
    response_model=CalificacionListResponse,
    dependencies=[Depends(check_permission("calificaciones:ver"))],
)
async def listar_calificaciones(
    materia_id: uuid.UUID,
    entrada_padron_id: uuid.UUID | None = Query(None),
    actividad: str | None = Query(None),
    aprobado: bool | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:ver")),
):
    repo = CalificacionesRepository(db)
    calificaciones, total = await repo.get_by_materia(
        materia_id=materia_id,
        tenant_id=user.tenant_id,
        entrada_padron_id=entrada_padron_id,
        actividad=actividad,
        aprobado=aprobado,
        offset=offset,
        limit=limit,
    )
    return {
        "calificaciones": [CalificacionRead.model_validate(c) for c in calificaciones],
        "total": total,
    }


@router.put(
    "/{materia_id}/umbral",
    response_model=UmbralUpdateResponse,
    dependencies=[Depends(check_permission("calificaciones:importar"))],
)
async def configurar_umbral(
    materia_id: uuid.UUID,
    request: UmbralUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:importar")),
):
    asignacion_id = await UmbralMateriaRepository.get_asignacion_id(
        db, user.id, materia_id, user.tenant_id,
    )
    if not asignacion_id:
        raise HTTPException(status_code=404, detail="No hay asignación activa para esta materia")

    repo = UmbralMateriaRepository(db)
    umbral = await repo.upsert(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=user.tenant_id,
        umbral_pct=request.umbral_pct,
        valores_aprobatorios=request.valores_aprobatorios,
    )
    return {
        "umbral_pct": umbral.umbral_pct,
        "valores_aprobatorios": umbral.valores_aprobatorios,
    }


@router.get(
    "/{materia_id}/umbral",
    response_model=UmbralRead,
    dependencies=[Depends(check_permission("calificaciones:ver"))],
)
async def obtener_umbral(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:ver")),
):
    asignacion_id = await UmbralMateriaRepository.get_asignacion_id(
        db, user.id, materia_id, user.tenant_id,
    )
    if not asignacion_id:
        return UmbralRead(
            umbral_pct=60,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
            es_defecto=True,
        )

    repo = UmbralMateriaRepository(db)
    umbral = await repo.get_by_asignacion_y_materia(asignacion_id, materia_id, user.tenant_id)

    if not umbral:
        return UmbralRead(
            umbral_pct=60,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
            es_defecto=True,
        )

    return UmbralRead(
        umbral_pct=umbral.umbral_pct,
        valores_aprobatorios=umbral.valores_aprobatorios,
        es_defecto=False,
    )


@router.post(
    "/{materia_id}/calificaciones/finalizacion/preview",
    response_model=FinalizacionPreviewResponse,
    dependencies=[Depends(check_permission("calificaciones:importar"))],
)
async def preview_finalizacion(
    materia_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:importar")),
):
    return await CalificacionesService.preview_finalizacion(materia_id, file, db, user)


@router.post(
    "/{materia_id}/calificaciones/finalizacion/confirm",
    response_model=FinalizacionConfirmResponse,
    dependencies=[Depends(check_permission("calificaciones:importar"))],
)
async def confirm_finalizacion(
    materia_id: uuid.UUID,
    request: FinalizacionConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:importar")),
):
    return await CalificacionesService.confirm_finalizacion(db, request.preview_token, user)


@router.delete(
    "/{materia_id}/calificaciones/datos",
    response_model=VaciarResponse,
    dependencies=[Depends(check_permission("calificaciones:vaciar"))],
)
async def vaciar_calificaciones(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("calificaciones:vaciar")),
):
    return await CalificacionesService.vaciar_datos(db, materia_id, user)
