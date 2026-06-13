from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.programa_materia import ProgramaMateria
from app.schemas.programa_materia import ProgramaMateriaListParams


class ProgramaMateriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> ProgramaMateria:
        obj = ProgramaMateria(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> ProgramaMateria | None:
        query = select(ProgramaMateria).where(
            ProgramaMateria.id == id,
            ProgramaMateria.tenant_id == tenant_id,
            ProgramaMateria.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, db_obj: ProgramaMateria, data: dict) -> ProgramaMateria:
        for key, value in data.items():
            if value is not None:
                setattr(db_obj, key, value)
        return db_obj

    async def delete(self, id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(ProgramaMateria).where(
            ProgramaMateria.id == id,
            ProgramaMateria.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        obj = result.scalar_one_or_none()
        if obj is not None:
            obj.deleted_at = datetime.now(timezone.utc)

    async def list(
        self,
        tenant_id: uuid.UUID,
        params: ProgramaMateriaListParams | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[ProgramaMateria], int]:
        conditions = [
            ProgramaMateria.tenant_id == tenant_id,
            ProgramaMateria.deleted_at.is_(None),
        ]

        if params is not None:
            if params.materia_id is not None:
                conditions.append(ProgramaMateria.materia_id == params.materia_id)
            if params.carrera_id is not None:
                conditions.append(ProgramaMateria.carrera_id == params.carrera_id)
            if params.cohorte_id is not None:
                conditions.append(ProgramaMateria.cohorte_id == params.cohorte_id)

        count_query = select(func.count()).select_from(ProgramaMateria).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(ProgramaMateria)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
            .order_by(ProgramaMateria.created_at.desc())
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def count(self, tenant_id: uuid.UUID) -> int:
        query = (
            select(func.count())
            .select_from(ProgramaMateria)
            .where(
                ProgramaMateria.tenant_id == tenant_id,
                ProgramaMateria.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
