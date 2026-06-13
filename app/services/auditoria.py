import uuid
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.asignacion import Asignacion
from app.models.user import User
from app.schemas.auditoria import AuditoriaLogParams


class AuditoriaService:

    @staticmethod
    async def get_metricas(db: AsyncSession, user: User) -> dict:
        acciones_por_dia_query = (
            select(
                func.date(AuditLog.created_at).label("fecha"),
                AuditLog.action,
                func.count().label("count"),
            )
            .group_by(func.date(AuditLog.created_at), AuditLog.action)
            .order_by(func.date(AuditLog.created_at).desc())
        )
        acciones_result = await db.execute(acciones_por_dia_query)
        acciones_por_dia = [
            {"fecha": str(row.fecha), "accion": row.action, "count": row.count}
            for row in acciones_result
        ]

        comunicaciones_query = (
            select(
                AuditLog.actor_id,
                func.count().label("total"),
            )
            .where(AuditLog.action.like("COMUNICACION_%"))
            .group_by(AuditLog.actor_id)
            .order_by(func.count().desc())
            .limit(50)
        )
        comunicaciones_result = await db.execute(comunicaciones_query)
        comunicaciones_por_docente = [
            {"usuario_id": row.actor_id, "nombre": row.actor_id, "total": row.total}
            for row in comunicaciones_result
        ]

        ultimas_query = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(200)
        )
        ultimas_result = await db.execute(ultimas_query)
        ultimas_acciones = list(ultimas_result.scalars().all())

        return {
            "acciones_por_dia": acciones_por_dia,
            "comunicaciones_por_docente": comunicaciones_por_docente,
            "ultimas_acciones": ultimas_acciones,
        }

    @staticmethod
    async def get_log(
        db: AsyncSession,
        params: AuditoriaLogParams,
        user: User,
    ) -> tuple[list[AuditLog], int]:
        base_query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        filters = []

        if params.fecha_desde:
            filters.append(AuditLog.created_at >= params.fecha_desde)
        if params.fecha_hasta:
            filters.append(AuditLog.created_at <= params.fecha_hasta)
        if params.materia_id:
            filters.append(AuditLog.materia_id == str(params.materia_id))
        if params.usuario_id:
            filters.append(AuditLog.actor_id == str(params.usuario_id))
        if params.accion:
            filters.append(AuditLog.action == params.accion)
        if params.estado:
            filters.append(AuditLog.status == params.estado)

        is_coordinador = any(
            ur.role.name == "COORDINADOR" for ur in user.user_roles
        )
        if is_coordinador:
            scope_materias = await AuditoriaService._get_user_materias(db, user)
            if scope_materias:
                filters.append(
                    or_(
                        AuditLog.materia_id.in_([str(m) for m in scope_materias]),
                        AuditLog.actor_id == str(user.id),
                    )
                )

        if filters:
            base_query = base_query.where(*filters)
            count_query = count_query.where(*filters)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        base_query = base_query.order_by(AuditLog.created_at.desc())
        base_query = base_query.offset(params.offset).limit(params.limit)

        result = await db.execute(base_query)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def _get_user_materias(db: AsyncSession, user: User) -> list[str]:
        stmt = select(Asignacion.contexto_id).where(
            Asignacion.user_id == user.id,
        )
        result = await db.execute(stmt)
        return [str(row) for row in result.scalars().all() if row]
