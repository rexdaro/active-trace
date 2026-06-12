from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.schemas.cohorte import CohorteCreate, CohorteRead
from app.models.cohorte import Cohorte
from app.models.user import User
from app.repositories.cohorte import CohorteRepository
import uuid

router = APIRouter(prefix="/api/cohortes", tags=["cohortes"])

@router.post("", response_model=CohorteRead, dependencies=[Depends(check_permission("estructura:gestionar"))])
async def create_cohorte(
    cohorte_in: CohorteCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar"))
):
    cohorte = Cohorte(
        **cohorte_in.model_dump(),
        tenant_id=user.tenant_id
    )
    repo = CohorteRepository(db)
    return await repo.create(cohorte)
