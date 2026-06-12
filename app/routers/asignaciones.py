from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.models.asignacion import Asignacion
from app.schemas.asignacion import AsignacionCreate, AsignacionRead

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])

@router.post("/", response_model=AsignacionRead, dependencies=[Depends(check_permission("equipos:asignar"))])
async def create_asignacion(
    asignacion: AsignacionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("equipos:asignar"))
):
    new_asignacion = Asignacion(
        tenant_id=user.tenant_id,
        **asignacion.model_dump()
    )
    db.add(new_asignacion)
    await db.commit()
    await db.refresh(new_asignacion)
    return new_asignacion
