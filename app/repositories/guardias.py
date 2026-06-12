from __future__ import annotations
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.guardia import Guardia
from app.models.asignacion import Asignacion


class GuardiaRepository(BaseRepository[Guardia]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Guardia)

    async def create(
        self,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        dia: str,
        horario: str,
        tenant_id: uuid.UUID,
        asignacion_id: uuid.UUID,
        comentarios: str | None = None,
    ) -> Guardia:
        guardia = Guardia(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            dia=dia,
            horario=horario,
            comentarios=comentarios,
            tenant_id=tenant_id,
        )
        self.session.add(guardia)
        return guardia

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Guardia], int]:
        query = select(Guardia).join(
            Asignacion, Guardia.asignacion_id == Asignacion.id,
        ).where(
            Asignacion.user_id == user_id,
            Guardia.tenant_id == tenant_id,
        )
        count_query = select(func.count()).select_from(Guardia).join(
            Asignacion, Guardia.asignacion_id == Asignacion.id,
        ).where(
            Asignacion.user_id == user_id,
            Guardia.tenant_id == tenant_id,
        )

        if materia_id is not None:
            query = query.where(Guardia.materia_id == materia_id)
            count_query = count_query.where(Guardia.materia_id == materia_id)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(offset).limit(limit).order_by(Guardia.created_at.desc())
        result = await self.session.execute(query)
        guardias = list(result.scalars().all())

        return guardias, total

    async def get_all(
        self,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Guardia], int]:
        query = select(Guardia).where(Guardia.tenant_id == tenant_id)
        count_query = select(func.count()).select_from(Guardia).where(
            Guardia.tenant_id == tenant_id,
        )

        if materia_id is not None:
            query = query.where(Guardia.materia_id == materia_id)
            count_query = count_query.where(Guardia.materia_id == materia_id)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(offset).limit(limit).order_by(Guardia.created_at.desc())
        result = await self.session.execute(query)
        guardias = list(result.scalars().all())

        return guardias, total

    async def update_guardia(
        self,
        id: uuid.UUID,
        data: dict,
        tenant_id: uuid.UUID,
    ) -> Guardia | None:
        query = select(Guardia).where(
            Guardia.id == id,
            Guardia.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        guardia = result.scalar_one_or_none()
        if guardia is None:
            return None
        for key, value in data.items():
            setattr(guardia, key, value)
        return guardia
