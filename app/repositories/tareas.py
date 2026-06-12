from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tarea import Tarea, ComentarioTarea, EstadoTarea
from app.schemas.tarea import TareaListParams


class TareaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, tenant_id: uuid.UUID) -> Tarea:
        obj = Tarea(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> Tarea | None:
        query = select(Tarea).where(
            Tarea.id == id,
            Tarea.tenant_id == tenant_id,
            Tarea.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, db_obj: Tarea, data: dict) -> Tarea:
        for key, value in data.items():
            if value is not None:
                setattr(db_obj, key, value)
        return db_obj

    async def delete(self, id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Tarea).where(
            Tarea.id == id,
            Tarea.tenant_id == tenant_id,
            Tarea.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        obj = result.scalar_one_or_none()
        if obj is not None:
            obj.deleted_at = datetime.now(timezone.utc)

    async def list_by_asignado(
        self,
        asignado_a: uuid.UUID,
        tenant_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Tarea], int]:
        conditions = [
            Tarea.tenant_id == tenant_id,
            Tarea.asignado_a == asignado_a,
            Tarea.deleted_at.is_(None),
        ]

        count_query = select(func.count()).select_from(Tarea).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(Tarea)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
            .order_by(Tarea.created_at.desc())
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def list_all(
        self,
        tenant_id: uuid.UUID,
        params: TareaListParams,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Tarea], int]:
        conditions = [Tarea.tenant_id == tenant_id, Tarea.deleted_at.is_(None)]

        if params.estado is not None:
            conditions.append(Tarea.estado == params.estado)
        if params.asignado_a is not None:
            conditions.append(Tarea.asignado_a == params.asignado_a)
        if params.materia_id is not None:
            conditions.append(Tarea.materia_id == params.materia_id)
        if params.search:
            conditions.append(Tarea.descripcion.ilike(f"%{params.search}%"))

        count_query = select(func.count()).select_from(Tarea).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(Tarea)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
            .order_by(Tarea.created_at.desc())
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def count_by_asignado(
        self, asignado_a: uuid.UUID, tenant_id: uuid.UUID
    ) -> int:
        conditions = [
            Tarea.tenant_id == tenant_id,
            Tarea.asignado_a == asignado_a,
            Tarea.deleted_at.is_(None),
        ]
        query = select(func.count()).select_from(Tarea).where(*conditions)
        result = await self.session.execute(query)
        return result.scalar() or 0

    # ─── Comentario methods ──────────────────────────────────────────────

    async def create_comentario(
        self, data: dict, tenant_id: uuid.UUID
    ) -> ComentarioTarea:
        obj = ComentarioTarea(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def list_comentarios(
        self, tarea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ComentarioTarea]:
        conditions = [
            ComentarioTarea.tarea_id == tarea_id,
            ComentarioTarea.tenant_id == tenant_id,
            ComentarioTarea.deleted_at.is_(None),
        ]
        query = (
            select(ComentarioTarea)
            .where(*conditions)
            .order_by(ComentarioTarea.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_comentario(
        self, id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ComentarioTarea | None:
        query = select(ComentarioTarea).where(
            ComentarioTarea.id == id,
            ComentarioTarea.tenant_id == tenant_id,
            ComentarioTarea.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete_comentario(self, id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(ComentarioTarea).where(
            ComentarioTarea.id == id,
            ComentarioTarea.tenant_id == tenant_id,
            ComentarioTarea.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        obj = result.scalar_one_or_none()
        if obj is not None:
            obj.deleted_at = datetime.now(timezone.utc)
