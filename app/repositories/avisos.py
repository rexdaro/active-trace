from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso
from app.schemas.aviso import AvisoListParams


class AvisoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, data: dict, tenant_id: uuid.UUID, usuario_id: uuid.UUID | None = None
    ) -> Aviso:
        obj = Aviso(**data, tenant_id=tenant_id)
        self.session.add(obj)
        return obj

    async def update(self, db_obj: Aviso, data: dict) -> Aviso:
        for key, value in data.items():
            if value is not None:
                setattr(db_obj, key, value)
        return db_obj

    async def delete(self, id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Aviso).where(Aviso.id == id, Aviso.tenant_id == tenant_id)
        result = await self.session.execute(query)
        obj = result.scalar_one_or_none()
        if obj is not None:
            await self.session.delete(obj)

    async def get(self, id: uuid.UUID, tenant_id: uuid.UUID) -> Aviso | None:
        query = select(Aviso).where(Aviso.id == id, Aviso.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_visibles(
        self,
        tenant_id: uuid.UUID,
        usuario_rol: str | None = None,
        usuario_id: uuid.UUID | None = None,
        materia_ids: list[uuid.UUID] | None = None,
        cohorte_ids: list[uuid.UUID] | None = None,
    ) -> list[Aviso]:
        now = datetime.now(timezone.utc)
        conditions = [
            Aviso.tenant_id == tenant_id,
            Aviso.activo == True,
            Aviso.inicio_en <= now,
            Aviso.fin_en >= now,
        ]

        alcance_conditions = [Aviso.alcance == AlcanceAviso.GLOBAL.value]

        if usuario_rol is not None:
            alcance_conditions.append(
                and_(
                    Aviso.alcance == AlcanceAviso.POR_ROL.value,
                    Aviso.rol_destino == usuario_rol,
                )
            )

        if materia_ids:
            alcance_conditions.append(
                and_(
                    Aviso.alcance == AlcanceAviso.POR_MATERIA.value,
                    Aviso.materia_id.in_(materia_ids),
                )
            )

        if cohorte_ids:
            alcance_conditions.append(
                and_(
                    Aviso.alcance == AlcanceAviso.POR_COHORTE.value,
                    Aviso.cohorte_id.in_(cohorte_ids),
                )
            )

        conditions.append(or_(*alcance_conditions))

        query = (
            select(Aviso)
            .where(*conditions)
            .order_by(Aviso.orden.asc(), Aviso.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        tenant_id: uuid.UUID,
        params: AvisoListParams,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Aviso], int]:
        conditions = [Aviso.tenant_id == tenant_id]

        if params.alcance is not None:
            conditions.append(Aviso.alcance == params.alcance)
        if params.materia_id is not None:
            conditions.append(Aviso.materia_id == params.materia_id)
        if params.cohorte_id is not None:
            conditions.append(Aviso.cohorte_id == params.cohorte_id)
        if params.rol_destino is not None:
            conditions.append(Aviso.rol_destino == params.rol_destino)
        if params.severidad is not None:
            conditions.append(Aviso.severidad == params.severidad)
        if params.activo is not None:
            conditions.append(Aviso.activo == params.activo)
        if not params.incluir_vencidos:
            now = datetime.now(timezone.utc)
            conditions.append(Aviso.fin_en >= now)

        count_query = select(func.count()).select_from(Aviso).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(Aviso)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
            .order_by(Aviso.created_at.desc())
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def count_visibles(
        self,
        tenant_id: uuid.UUID,
        usuario_rol: str | None = None,
        usuario_id: uuid.UUID | None = None,
        materia_ids: list[uuid.UUID] | None = None,
        cohorte_ids: list[uuid.UUID] | None = None,
    ) -> int:
        now = datetime.now(timezone.utc)
        conditions = [
            Aviso.tenant_id == tenant_id,
            Aviso.activo == True,
            Aviso.inicio_en <= now,
            Aviso.fin_en >= now,
        ]

        alcance_conditions = [Aviso.alcance == AlcanceAviso.GLOBAL.value]

        if usuario_rol is not None:
            alcance_conditions.append(
                and_(
                    Aviso.alcance == AlcanceAviso.POR_ROL.value,
                    Aviso.rol_destino == usuario_rol,
                )
            )

        if materia_ids:
            alcance_conditions.append(
                and_(
                    Aviso.alcance == AlcanceAviso.POR_MATERIA.value,
                    Aviso.materia_id.in_(materia_ids),
                )
            )

        if cohorte_ids:
            alcance_conditions.append(
                and_(
                    Aviso.alcance == AlcanceAviso.POR_COHORTE.value,
                    Aviso.cohorte_id.in_(cohorte_ids),
                )
            )

        conditions.append(or_(*alcance_conditions))

        query = select(func.count()).select_from(Aviso).where(*conditions)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create_ack(
        self, aviso_id: uuid.UUID, usuario_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> AcknowledgmentAviso:
        ack = AcknowledgmentAviso(
            id=uuid.uuid4(),
            aviso_id=aviso_id,
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            confirmado_at=datetime.now(timezone.utc),
        )
        self.session.add(ack)
        return ack

    async def get_ack(
        self, aviso_id: uuid.UUID, usuario_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> AcknowledgmentAviso | None:
        query = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.usuario_id == usuario_id,
            AcknowledgmentAviso.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ack_count(self, aviso_id: uuid.UUID, tenant_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_visto_count(self, aviso_id: uuid.UUID, tenant_id: uuid.UUID) -> int:
        return await self.get_ack_count(aviso_id, tenant_id)

    async def list_acks_for_aviso(
        self,
        aviso_id: uuid.UUID,
        tenant_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[AcknowledgmentAviso], int]:
        conditions = [
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.tenant_id == tenant_id,
        ]

        count_query = select(func.count()).select_from(AcknowledgmentAviso).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(AcknowledgmentAviso)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
            .order_by(AcknowledgmentAviso.confirmado_at)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total
