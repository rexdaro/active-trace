import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.salario import (
    SalarioBaseCreate,
    SalarioBaseUpdate,
    SalarioBaseResponse,
    SalarioPlusCreate,
    SalarioPlusUpdate,
    SalarioPlusResponse,
)
from app.repositories.salarios import SalarioBaseRepository, SalarioPlusRepository

router = APIRouter(prefix="/api/v1/salarios", tags=["Salarios"])


@router.get(
    "",
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def listar_salarios(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo_base = SalarioBaseRepository(db)
    repo_plus = SalarioPlusRepository(db)
    bases = await repo_base.list(user.tenant_id)
    pluses = await repo_plus.list(user.tenant_id)
    return {"bases": bases, "pluses": pluses}


@router.get(
    "/base",
    response_model=list[SalarioBaseResponse],
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def listar_salarios_base(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo = SalarioBaseRepository(db)
    return await repo.list(user.tenant_id)


@router.post(
    "/base",
    response_model=SalarioBaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def crear_salario_base(
    body: SalarioBaseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo = SalarioBaseRepository(db)
    obj = await repo.create(body.model_dump(), user.tenant_id)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/base/{salario_id}",
    response_model=SalarioBaseResponse,
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def actualizar_salario_base(
    salario_id: uuid.UUID,
    body: SalarioBaseUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo = SalarioBaseRepository(db)
    obj = await repo.get(salario_id, user.tenant_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SalarioBase no encontrado")
    await repo.update(obj, body.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/plus",
    response_model=list[SalarioPlusResponse],
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def listar_salarios_plus(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo = SalarioPlusRepository(db)
    return await repo.list(user.tenant_id)


@router.post(
    "/plus",
    response_model=SalarioPlusResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def crear_salario_plus(
    body: SalarioPlusCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo = SalarioPlusRepository(db)
    obj = await repo.create(body.model_dump(), user.tenant_id)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/plus/{salario_id}",
    response_model=SalarioPlusResponse,
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def actualizar_salario_plus(
    salario_id: uuid.UUID,
    body: SalarioPlusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    repo = SalarioPlusRepository(db)
    obj = await repo.get(salario_id, user.tenant_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SalarioPlus no encontrado")
    await repo.update(obj, body.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(obj)
    return obj
