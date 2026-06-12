from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.equipos import (
    AsignacionMasivaRequest, AsignacionMasivaResponse,
    ClonarRequest, ClonarResponse,
    ModificarVigenciaRequest, ModificarVigenciaResponse,
    AsignacionReadWithAttributes,
)
from app.services.equipos import EquiposService
import uuid

router = APIRouter(prefix="/api/equipos", tags=["equipos"])


@router.get(
    "/mis-equipos",
    response_model=list[AsignacionReadWithAttributes],
    dependencies=[Depends(check_permission("equipos:asignar"))],
)
async def mis_equipos(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar")),
):
    return await EquiposService.mis_equipos(db, user)


@router.get(
    "",
    response_model=list[AsignacionReadWithAttributes],
    dependencies=[Depends(check_permission("equipos:asignar"))],
)
async def listar_equipos(
    materia_id: uuid.UUID | None = Query(None),
    carrera_id: uuid.UUID | None = Query(None),
    cohorte_id: uuid.UUID | None = Query(None),
    role_id: int | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    vigente: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar")),
):
    return await EquiposService.listar(
        db, user,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        role_id=role_id,
        user_id=user_id,
        vigente=vigente,
    )


@router.post(
    "/asignacion-masiva",
    response_model=AsignacionMasivaResponse,
    dependencies=[Depends(check_permission("equipos:asignar"))],
)
async def asignacion_masiva(
    request: AsignacionMasivaRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar")),
):
    if not request.asignaciones:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La lista de asignaciones no puede estar vacía",
        )
    return await EquiposService.asignar_masiva(db, user, request)


@router.post(
    "/clonar",
    response_model=ClonarResponse,
    dependencies=[Depends(check_permission("equipos:asignar"))],
)
async def clonar_equipo(
    request: ClonarRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar")),
):
    return await EquiposService.clonar(db, user, request)


@router.put(
    "/vigencia",
    response_model=ModificarVigenciaResponse,
    dependencies=[Depends(check_permission("equipos:asignar"))],
)
async def modificar_vigencia(
    request: ModificarVigenciaRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar")),
):
    return await EquiposService.modificar_vigencia(db, user, request)


@router.get(
    "/export",
    dependencies=[Depends(check_permission("equipos:asignar"))],
)
async def exportar_equipo(
    contexto_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar")),
):
    csv_content = await EquiposService.exportar(db, user, contexto_id)
    filename = f"equipo-{contexto_id}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
