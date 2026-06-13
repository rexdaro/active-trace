import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import check_permission
from app.models.user import User
from app.schemas.liquidacion import LiquidacionResponse, CalcularLiquidacionRequest
from app.services.liquidaciones import LiquidacionService

router = APIRouter(prefix="/api/v1/liquidaciones", tags=["Liquidaciones"])


@router.get(
    "",
    response_model=list[LiquidacionResponse],
    dependencies=[Depends(check_permission("liquidaciones:ver"))],
)
async def listar_liquidaciones(
    periodo: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:ver")),
):
    return await LiquidacionService.listar(db, user.tenant_id, periodo)


@router.post(
    "/calcular",
    response_model=list[LiquidacionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permission("liquidaciones:configurar-salarios"))],
)
async def calcular_liquidaciones(
    body: CalcularLiquidacionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:configurar-salarios")),
):
    return await LiquidacionService.calcular(db, body.periodo, user.tenant_id, str(user.id))


@router.post(
    "/{liquidacion_id}/cerrar",
    response_model=LiquidacionResponse,
    dependencies=[Depends(check_permission("liquidaciones:cerrar"))],
)
async def cerrar_liquidacion(
    liquidacion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:cerrar")),
):
    return await LiquidacionService.cerrar(db, liquidacion_id, user.tenant_id, str(user.id))


@router.get(
    "/historial",
    response_model=list[LiquidacionResponse],
    dependencies=[Depends(check_permission("liquidaciones:ver"))],
)
async def historial_liquidaciones(
    usuario_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_permission("liquidaciones:ver")),
):
    return await LiquidacionService.get_historial(db, user.tenant_id, usuario_id)
