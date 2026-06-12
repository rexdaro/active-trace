from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import check_permission
from app.schemas.materia import MateriaCreate, MateriaRead
from app.models.materia import Materia
from app.models.user import User
from app.repositories.materia import MateriaRepository
import uuid

router = APIRouter(tags=["materias"])

@router.post("", response_model=MateriaRead, dependencies=[Depends(check_permission("estructura:gestionar"))])
async def create_materia(
    materia_in: MateriaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("estructura:gestionar"))
):
    materia = Materia(
        **materia_in.model_dump(),
        tenant_id=user.tenant_id
    )
    repo = MateriaRepository(db)
    return await repo.create(materia)
