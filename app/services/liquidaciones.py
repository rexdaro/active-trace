from __future__ import annotations
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import Liquidacion, Factura, EstadoLiquidacion, EstadoFactura
from app.models.asignacion import Asignacion
from app.repositories.liquidaciones import LiquidacionRepository, FacturaRepository
from app.repositories.salarios import SalarioBaseRepository
from app.services.audit import AuditService
from app.schemas.factura import FacturaCreate


class LiquidacionService:

    @staticmethod
    async def calcular(db: AsyncSession, periodo: str, tenant_id: uuid.UUID, user_id: str) -> list[Liquidacion]:
        repo = LiquidacionRepository(db)
        salario_base_repo = SalarioBaseRepository(db)

        periodo_date = _parse_periodo(periodo)

        asignaciones_query = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.desde <= periodo_date,
            or_(
                Asignacion.hasta.is_(None),
                Asignacion.hasta >= periodo_date,
            ),
        )
        result = await db.execute(asignaciones_query)
        asignaciones = list(result.scalars().all())

        liquidaciones = []
        for asignacion in asignaciones:
            salario_base = await salario_base_repo.get_vigente(
                tenant_id, str(asignacion.role_id), periodo_date
            )
            monto_base = salario_base.monto if salario_base else Decimal("0")

            liquidacion = await repo.create(
                {
                    "cohorte_id": asignacion.contexto_id,
                    "periodo": periodo,
                    "usuario_id": asignacion.user_id,
                    "rol": str(asignacion.role_id),
                    "monto_base": monto_base,
                    "monto_plus": Decimal("0"),
                    "total": monto_base,
                    "es_nexo": False,
                },
                tenant_id,
            )
            liquidaciones.append(liquidacion)

        await db.commit()

        await AuditService.log_action(
            db=db,
            action="LIQUIDACION_CALCULAR",
            user_id=user_id,
            resource="liquidaciones",
            status="success",
            actor_id=user_id,
            detalle={"periodo": periodo, "cantidad": len(liquidaciones)},
        )

        return liquidaciones

    @staticmethod
    async def cerrar(db: AsyncSession, id: uuid.UUID, tenant_id: uuid.UUID, user_id: str) -> Liquidacion:
        repo = LiquidacionRepository(db)
        liquidacion = await repo.get(id, tenant_id)
        if not liquidacion:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Liquidacion no encontrada")
        if liquidacion.estado == EstadoLiquidacion.CERRADA.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Liquidacion ya está cerrada")

        liquidacion.estado = EstadoLiquidacion.CERRADA.value
        await db.commit()
        await db.refresh(liquidacion)

        await AuditService.log_action(
            db=db,
            action="LIQUIDACION_CERRAR",
            user_id=user_id,
            resource="liquidaciones",
            status="success",
            actor_id=user_id,
            detalle={"liquidacion_id": str(id), "periodo": liquidacion.periodo},
        )

        return liquidacion

    @staticmethod
    async def listar(db: AsyncSession, tenant_id: uuid.UUID, periodo: str | None = None) -> list[Liquidacion]:
        repo = LiquidacionRepository(db)
        return await repo.list(tenant_id, periodo)

    @staticmethod
    async def get_historial(
        db: AsyncSession, tenant_id: uuid.UUID, usuario_id: uuid.UUID | None = None
    ) -> list[Liquidacion]:
        repo = LiquidacionRepository(db)
        return await repo.list_historial(tenant_id, usuario_id)


class FacturaService:

    @staticmethod
    async def crear(db: AsyncSession, obj_in: FacturaCreate, tenant_id: uuid.UUID, user_id: str) -> Factura:
        repo = FacturaRepository(db)
        data = obj_in.model_dump()
        factura = await repo.create(data, tenant_id)
        await db.commit()
        await db.refresh(factura)

        await AuditService.log_action(
            db=db,
            action="FACTURA_CREAR",
            user_id=user_id,
            resource="facturas",
            status="success",
            actor_id=user_id,
            detalle={"factura_id": str(factura.id), "periodo": obj_in.periodo},
        )

        return factura

    @staticmethod
    async def abonar(db: AsyncSession, id: uuid.UUID, tenant_id: uuid.UUID, user_id: str) -> Factura:
        repo = FacturaRepository(db)
        factura = await repo.get(id, tenant_id)
        if not factura:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
        if factura.estado == EstadoFactura.ABONADA.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Factura ya está abonada")

        factura.estado = EstadoFactura.ABONADA.value
        factura.abonada_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(factura)

        await AuditService.log_action(
            db=db,
            action="FACTURA_ABONAR",
            user_id=user_id,
            resource="facturas",
            status="success",
            actor_id=user_id,
            detalle={"factura_id": str(id)},
        )

        return factura

    @staticmethod
    async def listar(db: AsyncSession, tenant_id: uuid.UUID, periodo: str | None = None) -> list[Factura]:
        repo = FacturaRepository(db)
        return await repo.list(tenant_id, periodo)


def _parse_periodo(periodo: str) -> date:
    parts = periodo.split("-")
    return date(int(parts[0]), int(parts[1]), 1)
