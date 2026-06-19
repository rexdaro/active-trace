import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.tarea import (
    TareaCreate,
    TareaUpdate,
    TareaEstadoUpdate,
    TareaResponse,
    TareaListParams,
    ComentarioTareaCreate,
    ComentarioTareaResponse,
)
from app.services.tareas import TareaService

router = APIRouter(prefix="/api/v1/tareas", tags=["Tareas"])


# ─── Static routes BEFORE parameterized ─────────────────────────────────


@router.get(
    "",
    response_model=list[TareaResponse],
    dependencies=[Depends(check_permission("tareas:ver"))],
)
async def listar_tareas(
    estado: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:ver")),
):
    params = TareaListParams(estado=estado)
    items, _total = await TareaService.list_all_tareas(db, user, params, offset, limit)
    return items


@router.post(
    "",
    response_model=TareaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("tareas:crear"))],
)
async def crear_tarea(
    body: TareaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:crear")),
):
    return await TareaService.create(db, body, user)


@router.get(
    "/mis-tareas",
    response_model=list[TareaResponse],
    dependencies=[Depends(check_permission("tareas:ver"))],
)
async def listar_mis_tareas(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:ver")),
):
    items, _total = await TareaService.list_mis_tareas(db, user, offset, limit)
    return items


@router.get(
    "/admin",
    response_model=list[TareaResponse],
    dependencies=[Depends(check_permission("tareas:gestionar"))],
)
async def listar_tareas_admin(
    estado: str | None = Query(None),
    asignado_a: uuid.UUID | None = Query(None),
    materia_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:gestionar")),
):
    params = TareaListParams(
        estado=estado,
        asignado_a=asignado_a,
        materia_id=materia_id,
        search=search,
    )
    items, _total = await TareaService.list_all_tareas(db, user, params, offset, limit)
    return items


# ─── Parameterized routes ────────────────────────────────────────────────


@router.get(
    "/{tarea_id}",
    response_model=TareaResponse,
    dependencies=[Depends(check_permission("tareas:ver"))],
)
async def obtener_tarea(
    tarea_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:ver")),
):
    return await TareaService.get(db, tarea_id, user)


@router.put(
    "/{tarea_id}",
    response_model=TareaResponse,
    dependencies=[Depends(check_permission("tareas:crear"))],
)
async def actualizar_tarea(
    tarea_id: uuid.UUID,
    body: TareaUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:crear")),
):
    return await TareaService.update(db, tarea_id, body, user)


@router.put(
    "/{tarea_id}/estado",
    response_model=TareaResponse,
    dependencies=[Depends(check_permission("tareas:ver"))],
)
async def actualizar_estado_tarea(
    tarea_id: uuid.UUID,
    body: TareaEstadoUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:ver")),
):
    return await TareaService.update(db, tarea_id, body, user)


@router.delete(
    "/{tarea_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permission("tareas:gestionar"))],
)
async def eliminar_tarea(
    tarea_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:gestionar")),
):
    await TareaService.delete(db, tarea_id, user)


@router.post(
    "/{tarea_id}/comentarios",
    response_model=ComentarioTareaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("tareas:ver"))],
)
async def agregar_comentario(
    tarea_id: uuid.UUID,
    body: ComentarioTareaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:ver")),
):
    return await TareaService.add_comentario(db, tarea_id, body, user)


@router.get(
    "/{tarea_id}/comentarios",
    response_model=list[ComentarioTareaResponse],
    dependencies=[Depends(check_permission("tareas:ver"))],
)
async def listar_comentarios(
    tarea_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:ver")),
):
    return await TareaService.list_comentarios(db, tarea_id, user)


@router.delete(
    "/{tarea_id}/comentarios/{comentario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permission("tareas:gestionar"))],
)
async def eliminar_comentario(
    tarea_id: uuid.UUID,
    comentario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("tareas:gestionar")),
):
    await TareaService.delete_comentario(db, tarea_id, comentario_id, user)
