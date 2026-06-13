import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.factura import FacturaCreate, FacturaResponse
from app.services.liquidaciones import FacturaService

router = APIRouter(prefix="/api/v1/facturas", tags=["Facturas"])


@router.get(
    "",
    response_model=list[FacturaResponse],
    dependencies=[Depends(check_permission("liquidaciones:ver"))],
)
async def listar_facturas(
    periodo: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:ver")),
):
    return await FacturaService.listar(db, user.tenant_id, periodo)


@router.post(
    "",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("liquidaciones:ver"))],
)
async def crear_factura(
    body: FacturaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:ver")),
):
    return await FacturaService.crear(db, body, user.tenant_id, str(user.id))


@router.put(
    "/{factura_id}/abonar",
    response_model=FacturaResponse,
    dependencies=[Depends(check_permission("liquidaciones:cerrar"))],
)
async def abonar_factura(
    factura_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:cerrar")),
):
    return await FacturaService.abonar(db, factura_id, user.tenant_id, str(user.id))
