from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.liquidacion import Liquidacion, Factura, EstadoLiquidacion, EstadoFactura


class LiquidacionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> Liquidacion:
        obj = Liquidacion(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> Liquidacion | None:
        query = select(Liquidacion).where(Liquidacion.id == id, Liquidacion.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: uuid.UUID,
        periodo: str | None = None,
        usuario_id: uuid.UUID | None = None,
    ) -> list[Liquidacion]:
        conditions = [Liquidacion.tenant_id == tenant_id]
        if periodo:
            conditions.append(Liquidacion.periodo == periodo)
        if usuario_id:
            conditions.append(Liquidacion.usuario_id == usuario_id)

        query = (
            select(Liquidacion)
            .where(*conditions)
            .order_by(Liquidacion.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_historial(
        self,
        tenant_id: uuid.UUID,
        usuario_id: uuid.UUID | None = None,
    ) -> list[Liquidacion]:
        conditions = [Liquidacion.tenant_id == tenant_id]
        if usuario_id:
            conditions.append(Liquidacion.usuario_id == usuario_id)

        query = (
            select(Liquidacion)
            .where(*conditions)
            .order_by(Liquidacion.periodo.desc(), Liquidacion.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, tenant_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(Liquidacion).where(Liquidacion.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar() or 0


class FacturaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> Factura:
        obj = Factura(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> Factura | None:
        query = select(Factura).where(Factura.id == id, Factura.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(self, tenant_id: uuid.UUID, periodo: str | None = None) -> list[Factura]:
        conditions = [Factura.tenant_id == tenant_id]
        if periodo:
            conditions.append(Factura.periodo == periodo)

        query = (
            select(Factura)
            .where(*conditions)
            .order_by(Factura.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, tenant_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(Factura).where(Factura.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar() or 0
