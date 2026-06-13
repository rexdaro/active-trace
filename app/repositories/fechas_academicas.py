from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fecha_academica import FechaAcademica
from app.schemas.fecha_academica import FechaAcademicaListParams


class FechaAcademicaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> FechaAcademica:
        obj = FechaAcademica(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> FechaAcademica | None:
        query = select(FechaAcademica).where(
            FechaAcademica.id == id,
            FechaAcademica.tenant_id == tenant_id,
            FechaAcademica.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, db_obj: FechaAcademica, data: dict) -> FechaAcademica:
        for key, value in data.items():
            if value is not None:
                setattr(db_obj, key, value)
        return db_obj

    async def delete(self, id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(FechaAcademica).where(
            FechaAcademica.id == id,
            FechaAcademica.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        obj = result.scalar_one_or_none()
        if obj is not None:
            obj.deleted_at = datetime.now(timezone.utc)

    async def list(
        self,
        tenant_id: uuid.UUID,
        params: FechaAcademicaListParams | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[FechaAcademica], int]:
        conditions = [
            FechaAcademica.tenant_id == tenant_id,
            FechaAcademica.deleted_at.is_(None),
        ]

        if params is not None:
            if params.materia_id is not None:
                conditions.append(FechaAcademica.materia_id == params.materia_id)
            if params.cohorte_id is not None:
                conditions.append(FechaAcademica.cohorte_id == params.cohorte_id)
            if params.tipo is not None:
                conditions.append(FechaAcademica.tipo == params.tipo)
            if params.periodo is not None:
                conditions.append(FechaAcademica.periodo == params.periodo)

        count_query = select(func.count()).select_from(FechaAcademica).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(FechaAcademica)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
            .order_by(FechaAcademica.created_at.desc())
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def list_html(
        self,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
    ) -> list[FechaAcademica]:
        query = (
            select(FechaAcademica)
            .where(
                FechaAcademica.tenant_id == tenant_id,
                FechaAcademica.materia_id == materia_id,
                FechaAcademica.cohorte_id == cohorte_id,
                FechaAcademica.deleted_at.is_(None),
            )
            .order_by(FechaAcademica.fecha.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, tenant_id: uuid.UUID) -> int:
        query = (
            select(func.count())
            .select_from(FechaAcademica)
            .where(
                FechaAcademica.tenant_id == tenant_id,
                FechaAcademica.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
