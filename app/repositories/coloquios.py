from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.coloquio import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, EstadoReserva
from app.schemas.coloquio import PanelMetricas


class ColoquiosRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Evaluacion ──────────────────────────────────────────────────────────

    async def crear_evaluacion(self, data: dict) -> Evaluacion:
        ev = Evaluacion(**data)
        self.session.add(ev)
        return ev

    async def get_evaluacion(self, id: uuid.UUID, tenant_id: uuid.UUID) -> Evaluacion | None:
        query = select(Evaluacion).where(
            Evaluacion.id == id,
            Evaluacion.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_evaluaciones(
        self,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Evaluacion], int]:
        base_where = [Evaluacion.tenant_id == tenant_id]
        if materia_id is not None:
            base_where.append(Evaluacion.materia_id == materia_id)

        count_query = select(func.count()).select_from(Evaluacion).where(*base_where)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(Evaluacion)
            .where(*base_where)
            .offset(offset)
            .limit(limit)
            .order_by(Evaluacion.created_at)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_evaluaciones_activas(self, tenant_id: uuid.UUID) -> list[Evaluacion]:
        query = select(Evaluacion).where(Evaluacion.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ── Reserva ─────────────────────────────────────────────────────────────

    async def crear_reserva(self, data: dict) -> ReservaEvaluacion:
        res = ReservaEvaluacion(**data)
        self.session.add(res)
        return res

    async def get_reserva(self, id: uuid.UUID, tenant_id: uuid.UUID) -> ReservaEvaluacion | None:
        query = select(ReservaEvaluacion).where(
            ReservaEvaluacion.id == id,
            ReservaEvaluacion.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_reservas_by_evaluacion(
        self,
        evaluacion_id: uuid.UUID,
        tenant_id: uuid.UUID,
        estado: str | None = None,
    ) -> list[ReservaEvaluacion]:
        where = [
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == tenant_id,
        ]
        if estado is not None:
            where.append(ReservaEvaluacion.estado == estado)
        query = select(ReservaEvaluacion).where(*where).order_by(ReservaEvaluacion.fecha_hora)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_reservas_by_alumno(
        self,
        alumno_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[ReservaEvaluacion]:
        query = select(ReservaEvaluacion).where(
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.tenant_id == tenant_id,
        ).order_by(ReservaEvaluacion.fecha_hora)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_reservas_activas_by_alumno(
        self,
        alumno_id: uuid.UUID,
        evaluacion_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[ReservaEvaluacion]:
        query = select(ReservaEvaluacion).where(
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == tenant_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA.value,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def cancelar_reserva(
        self,
        id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> ReservaEvaluacion | None:
        query = select(ReservaEvaluacion).where(
            ReservaEvaluacion.id == id,
            ReservaEvaluacion.tenant_id == tenant_id,
        )
        result = await self.session.execute(query)
        res = result.scalar_one_or_none()
        if res is None:
            return None
        res.estado = EstadoReserva.CANCELADA.value
        return res

    async def count_reservas_activas_by_evaluacion_y_fecha(
        self,
        evaluacion_id: uuid.UUID,
        fecha_hora: datetime,
        tenant_id: uuid.UUID,
    ) -> int:
        query = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.fecha_hora == fecha_hora,
            ReservaEvaluacion.tenant_id == tenant_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA.value,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    # ── Resultado ───────────────────────────────────────────────────────────

    async def crear_resultado(self, data: dict) -> ResultadoEvaluacion:
        res = ResultadoEvaluacion(**data)
        self.session.add(res)
        return res

    async def get_resultados_by_evaluacion(
        self,
        evaluacion_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[ResultadoEvaluacion]:
        query = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.tenant_id == tenant_id,
        ).order_by(ResultadoEvaluacion.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ── Metrics ─────────────────────────────────────────────────────────────

    async def get_panel_metricas(self, tenant_id: uuid.UUID) -> PanelMetricas:
        ev_count = select(func.count()).select_from(Evaluacion).where(
            Evaluacion.tenant_id == tenant_id,
        )
        res_count = select(func.count()).select_from(ReservaEvaluacion).where(
            and_(
                ReservaEvaluacion.tenant_id == tenant_id,
                ReservaEvaluacion.estado == EstadoReserva.ACTIVA.value,
            )
        )
        rdo_count = select(func.count()).select_from(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == tenant_id,
        )
        alumnos_count = select(func.count(func.distinct(ReservaEvaluacion.alumno_id))).select_from(
            ReservaEvaluacion
        ).where(ReservaEvaluacion.tenant_id == tenant_id)

        ev_result = await self.session.execute(ev_count)
        res_result = await self.session.execute(res_count)
        rdo_result = await self.session.execute(rdo_count)
        alum_result = await self.session.execute(alumnos_count)

        return PanelMetricas(
            total_evaluaciones=ev_result.scalar() or 0,
            total_reservas_activas=res_result.scalar() or 0,
            total_resultados=rdo_result.scalar() or 0,
            total_alumnos_convocados=alum_result.scalar() or 0,
        )
