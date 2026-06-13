from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.salario import SalarioBase, SalarioPlus


class SalarioBaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> SalarioBase:
        obj = SalarioBase(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def update(self, db_obj: SalarioBase, data: dict) -> SalarioBase:
        for key, value in data.items():
            if value is not None:
                setattr(db_obj, key, value)
        return db_obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> SalarioBase | None:
        query = select(SalarioBase).where(SalarioBase.id == id, SalarioBase.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(self, tenant_id: uuid.UUID) -> list[SalarioBase]:
        query = (
            select(SalarioBase)
            .where(SalarioBase.tenant_id == tenant_id)
            .order_by(SalarioBase.rol, SalarioBase.desde.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_vigente(
        self, tenant_id: uuid.UUID, rol: str, referencia: date
    ) -> SalarioBase | None:
        query = select(SalarioBase).where(
            SalarioBase.tenant_id == tenant_id,
            SalarioBase.rol == rol,
            SalarioBase.desde <= referencia,
            or_(
                SalarioBase.hasta.is_(None),
                SalarioBase.hasta >= referencia,
            ),
        ).order_by(SalarioBase.desde.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count(self, tenant_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(SalarioBase).where(SalarioBase.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar() or 0


class SalarioPlusRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> SalarioPlus:
        obj = SalarioPlus(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def update(self, db_obj: SalarioPlus, data: dict) -> SalarioPlus:
        for key, value in data.items():
            if value is not None:
                setattr(db_obj, key, value)
        return db_obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> SalarioPlus | None:
        query = select(SalarioPlus).where(SalarioPlus.id == id, SalarioPlus.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(self, tenant_id: uuid.UUID) -> list[SalarioPlus]:
        query = (
            select(SalarioPlus)
            .where(SalarioPlus.tenant_id == tenant_id)
            .order_by(SalarioPlus.grupo, SalarioPlus.rol)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_aplicables(
        self, tenant_id: uuid.UUID, rol: str, grupo: str, referencia: date
    ) -> list[SalarioPlus]:
        query = select(SalarioPlus).where(
            SalarioPlus.tenant_id == tenant_id,
            SalarioPlus.rol == rol,
            SalarioPlus.grupo == grupo,
            SalarioPlus.desde <= referencia,
            or_(
                SalarioPlus.hasta.is_(None),
                SalarioPlus.hasta >= referencia,
            ),
        ).order_by(SalarioPlus.desde.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, tenant_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(SalarioPlus).where(SalarioPlus.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar() or 0
