from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func, case, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.models.tenant import Tenant


class ComunicacionesRepository(BaseRepository[Comunicacion]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Comunicacion)

    async def bulk_create(self, entries: list[dict]) -> list[Comunicacion]:
        comunicaciones = []
        for data in entries:
            c = Comunicacion(
                tenant_id=data["tenant_id"],
                enviado_por=data["enviado_por"],
                materia_id=data["materia_id"],
                destinatario=data["destinatario"],
                asunto=data["asunto"],
                cuerpo=data["cuerpo"],
                estado=data.get("estado", ComunicacionEstado.PENDIENTE.value),
                lote_id=data.get("lote_id"),
                lote_aprobado=data.get("lote_aprobado", False),
            )
            self.session.add(c)
            comunicaciones.append(c)
        return comunicaciones

    async def get_by_lote(self, lote_id: uuid.UUID, tenant_id: uuid.UUID) -> list[Comunicacion]:
        query = select(Comunicacion).where(
            Comunicacion.lote_id == lote_id,
            Comunicacion.tenant_id == tenant_id,
        ).order_by(Comunicacion.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_lotes(
        self,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        base_filters = [
            Comunicacion.tenant_id == tenant_id,
            Comunicacion.lote_id.isnot(None),
        ]
        if materia_id:
            base_filters.append(Comunicacion.materia_id == materia_id)

        count_subq = (
            select(Comunicacion.lote_id)
            .where(*base_filters)
            .group_by(Comunicacion.lote_id)
            .subquery()
        )
        count_query = select(func.count()).select_from(count_subq)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(
                Comunicacion.lote_id,
                Comunicacion.enviado_por,
                Comunicacion.materia_id,
                func.count().label("total"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.PENDIENTE.value, 1), else_=0)).label("pendientes"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ENVIANDO.value, 1), else_=0)).label("enviando"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ENVIADO.value, 1), else_=0)).label("enviados"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ERROR.value, 1), else_=0)).label("errores"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.CANCELADO.value, 1), else_=0)).label("cancelados"),
                func.max(Comunicacion.created_at).label("created_at"),
            )
            .where(*base_filters)
            .group_by(Comunicacion.lote_id, Comunicacion.enviado_por, Comunicacion.materia_id)
            .order_by(func.max(Comunicacion.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()

        lotes = []
        for row in rows:
            lotes.append({
                "lote_id": row.lote_id,
                "enviado_por": row.enviado_por,
                "materia_id": row.materia_id,
                "total": row.total,
                "pendientes": row.pendientes,
                "enviando": row.enviando,
                "enviados": row.enviados,
                "errores": row.errores,
                "cancelados": row.cancelados,
                "created_at": row.created_at,
            })

        return lotes, total

    async def get_lote_summary(self, lote_id: uuid.UUID, tenant_id: uuid.UUID) -> dict | None:
        query = (
            select(
                Comunicacion.lote_id,
                Comunicacion.enviado_por,
                Comunicacion.materia_id,
                func.count().label("total"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.PENDIENTE.value, 1), else_=0)).label("pendientes"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ENVIANDO.value, 1), else_=0)).label("enviando"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ENVIADO.value, 1), else_=0)).label("enviados"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ERROR.value, 1), else_=0)).label("errores"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.CANCELADO.value, 1), else_=0)).label("cancelados"),
                func.max(Comunicacion.created_at).label("created_at"),
            )
            .where(
                Comunicacion.lote_id == lote_id,
                Comunicacion.tenant_id == tenant_id,
            )
            .group_by(Comunicacion.lote_id, Comunicacion.enviado_por, Comunicacion.materia_id)
        )
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            return None
        return {
            "lote_id": row.lote_id,
            "enviado_por": row.enviado_por,
            "materia_id": row.materia_id,
            "total": row.total,
            "pendientes": row.pendientes,
            "enviando": row.enviando,
            "enviados": row.enviados,
            "errores": row.errores,
            "cancelados": row.cancelados,
            "created_at": row.created_at,
        }

    async def get_pendientes_elegibles(self, tenant_id: uuid.UUID, limit: int = 50) -> list[Comunicacion]:
        query = (
            select(Comunicacion)
            .join(Tenant, Comunicacion.tenant_id == Tenant.id)
            .where(
                Comunicacion.tenant_id == tenant_id,
                Comunicacion.estado == ComunicacionEstado.PENDIENTE.value,
                or_(
                    Tenant.requiere_aprobacion == False,
                    Comunicacion.lote_aprobado == True,
                ),
            )
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def transition_state(
        self,
        id: uuid.UUID,
        from_state: str,
        to_state: str,
        tenant_id: uuid.UUID,
    ) -> Comunicacion | None:
        query = select(Comunicacion).where(
            Comunicacion.id == id,
            Comunicacion.tenant_id == tenant_id,
            Comunicacion.estado == from_state,
        )
        result = await self.session.execute(query)
        comunicacion = result.scalar_one_or_none()
        if comunicacion is None:
            return None
        comunicacion.estado = to_state
        await self.session.flush()
        return comunicacion

    async def cancel_by_lote(self, lote_id: uuid.UUID, tenant_id: uuid.UUID) -> int:
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.lote_id == lote_id,
                Comunicacion.tenant_id == tenant_id,
                Comunicacion.estado == ComunicacionEstado.PENDIENTE.value,
            )
            .values(estado=ComunicacionEstado.CANCELADO.value)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def approve_by_lote(self, lote_id: uuid.UUID, tenant_id: uuid.UUID) -> int:
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.lote_id == lote_id,
                Comunicacion.tenant_id == tenant_id,
                Comunicacion.estado == ComunicacionEstado.PENDIENTE.value,
            )
            .values(
                lote_aprobado=True,
                estado=ComunicacionEstado.ENVIANDO.value,
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def approve_single(self, id: uuid.UUID, tenant_id: uuid.UUID) -> Comunicacion | None:
        query = select(Comunicacion).where(
            Comunicacion.id == id,
            Comunicacion.tenant_id == tenant_id,
            Comunicacion.estado == ComunicacionEstado.PENDIENTE.value,
        )
        result = await self.session.execute(query)
        comunicacion = result.scalar_one_or_none()
        if comunicacion is None:
            return None
        comunicacion.estado = ComunicacionEstado.ENVIANDO.value
        await self.session.flush()
        return comunicacion

    async def get_estados_panel(
        self,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID | None = None,
    ) -> list[dict]:
        from app.models.materia import Materia

        base_filters = [Comunicacion.tenant_id == tenant_id]
        if materia_id:
            base_filters.append(Comunicacion.materia_id == materia_id)

        query = (
            select(
                Comunicacion.materia_id,
                func.count().label("total"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.PENDIENTE.value, 1), else_=0)).label("pendientes"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ENVIANDO.value, 1), else_=0)).label("enviando"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ENVIADO.value, 1), else_=0)).label("enviados"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.ERROR.value, 1), else_=0)).label("errores"),
                func.sum(case((Comunicacion.estado == ComunicacionEstado.CANCELADO.value, 1), else_=0)).label("cancelados"),
            )
            .where(*base_filters)
            .group_by(Comunicacion.materia_id)
        )
        result = await self.session.execute(query)
        rows = result.all()

        materia_ids = [row.materia_id for row in rows]
        if materia_ids:
            materias_stmt = select(Materia).where(Materia.id.in_(materia_ids))
            materias_result = await self.session.execute(materias_stmt)
            materias_map = {m.id: m.name for m in materias_result.scalars().all()}
        else:
            materias_map = {}

        panel = []
        for row in rows:
            panel.append({
                "materia_id": row.materia_id,
                "materia_nombre": materias_map.get(row.materia_id, ""),
                "pendientes": row.pendientes,
                "enviando": row.enviando,
                "enviados": row.enviados,
                "errores": row.errores,
                "cancelados": row.cancelados,
            })

        return panel
