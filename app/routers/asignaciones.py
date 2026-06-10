from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.asignacion import Asignacion
from app.schemas.asignacion import AsignacionCreate, AsignacionRead
import uuid

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])

@router.post("/", response_model=AsignacionRead)
async def create_asignacion(asignacion: AsignacionCreate, db: AsyncSession = Depends(get_db)):
    new_asignacion = Asignacion(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        **asignacion.model_dump()
    )
    db.add(new_asignacion)
    await db.commit()
    await db.refresh(new_asignacion)
    return new_asignacion
