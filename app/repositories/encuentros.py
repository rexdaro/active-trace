from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlotEncuentro)

    async def create_slot(
        self,
        materia_id: uuid.UUID,
        creado_por: uuid.UUID,
        dia_semana: str,
        horario: str,
        titulo: str,
        fecha_inicio: date,
        cant_semanas: int,
        tenant_id: uuid.UUID,
        meet_url: str | None = None,
        activo: bool = True,
    ) -> SlotEncuentro:
        slot = SlotEncuentro(
            materia_id=materia_id,
            creado_por=creado_por,
            dia_semana=dia_semana,
            horario=horario,
            titulo=titulo,
            meet_url=meet_url,
            fecha_inicio=fecha_inicio,
            cant_semanas=cant_semanas,
            activo=activo,
            tenant_id=tenant_id,
        )
        self.session.add(slot)
        return slot

    async def get_by_materia(
        self,
        materia_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[SlotEncuentro]:
        query = select(SlotEncuentro).where(
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.materia_id == materia_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_activo(
        self,
        slot_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> SlotEncuentro | None:
        query = select(SlotEncuentro).where(
            SlotEncuentro.id == slot_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.activo == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, InstanciaEncuentro)

    async def create(
        self,
        materia_id: uuid.UUID,
        fecha: date,
        hora: str,
        titulo: str,
        tenant_id: uuid.UUID,
        slot_id: uuid.UUID | None = None,
        meet_url: str | None = None,
    ) -> InstanciaEncuentro:
        instancia = InstanciaEncuentro(
            slot_id=slot_id,
            materia_id=materia_id,
            fecha=fecha,
            hora=hora,
            titulo=titulo,
            meet_url=meet_url,
            tenant_id=tenant_id,
        )
        self.session.add(instancia)
        return instancia

    async def bulk_create(
        self,
        instances_data: list[dict],
    ) -> list[InstanciaEncuentro]:
        instancias = []
        for data in instances_data:
            instancia = InstanciaEncuentro(
                slot_id=data.get("slot_id"),
                materia_id=data["materia_id"],
                fecha=data["fecha"],
                hora=data["hora"],
                titulo=data["titulo"],
                meet_url=data.get("meet_url"),
                tenant_id=data["tenant_id"],
            )
            self.session.add(instancia)
            instancias.append(instancia)
        return instancias

    async def get_by_materia(
        self,
        materia_id: uuid.UUID,
        tenant_id: uuid.UUID,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[InstanciaEncuentro], int]:
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.materia_id == materia_id,
        )
        count_query = select(func.count()).select_from(InstanciaEncuentro).where(
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.materia_id == materia_id,
        )

        if estado is not None:
            query = query.where(InstanciaEncuentro.estado == estado)
            count_query = count_query.where(InstanciaEncuentro.estado == estado)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(offset).limit(limit).order_by(InstanciaEncuentro.fecha)
        result = await self.session.execute(query)
        instancias = list(result.scalars().all())

        return instancias, total

    async def get_by_slot(
        self,
        slot_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[InstanciaEncuentro]:
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.slot_id == slot_id,
            InstanciaEncuentro.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_instancia(
        self,
        id: uuid.UUID,
        data: dict,
        tenant_id: uuid.UUID,
    ) -> InstanciaEncuentro | None:
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.id == id,
            InstanciaEncuentro.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        instancia = result.scalar_one_or_none()
        if instancia is None:
            return None
        for key, value in data.items():
            setattr(instancia, key, value)
        return instancia
