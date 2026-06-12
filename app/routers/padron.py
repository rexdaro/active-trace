from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.padron import (
    PadronPreviewResponse,
    PadronConfirmRequest,
    PadronConfirmResponse,
    VersionPadronRead,
    VaciarResponse,
    SyncRequest,
    SyncResponse,
)
from app.services.padron import PadronService
from app.integrations.moodle_ws import MoodleWSService
import uuid

router = APIRouter(prefix="/api/v1/padron", tags=["padron"])


@router.post("/preview", response_model=PadronPreviewResponse, dependencies=[Depends(check_permission("padron:importar"))])
async def preview_padron(
    file: UploadFile = File(...),
    materia_id: uuid.UUID = Form(...),
    cohorte_id: uuid.UUID = Form(...),
    user: User = Depends(check_permission("padron:importar")),
):
    return await PadronService.preview(file, materia_id, cohorte_id)


@router.post("/confirm", response_model=PadronConfirmResponse, dependencies=[Depends(check_permission("padron:importar"))])
async def confirm_padron(
    request: PadronConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("padron:importar")),
):
    return await PadronService.confirm(db, request.preview_token, user)


@router.delete("/{materia_id}/datos", response_model=VaciarResponse, dependencies=[Depends(check_permission("padron:vaciar"))])
async def vaciar_padron(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("padron:vaciar")),
):
    return await PadronService.vaciar_datos(db, materia_id, user)


@router.get("/{materia_id}/versiones", response_model=list[VersionPadronRead], dependencies=[Depends(check_permission("padron:ver"))])
async def listar_versiones(
    materia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("padron:ver")),
):
    return await PadronService.get_versiones(db, materia_id, user)


@router.post("/sync", response_model=SyncResponse, dependencies=[Depends(check_permission("padron:sincronizar"))])
async def sync_padron(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("padron:sincronizar")),
):
    result = await MoodleWSService.sync_from_moodle(db, user, request.materia_id)
    return result
