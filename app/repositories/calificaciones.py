import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.calificacion import Calificacion, CalificacionOrigen


class CalificacionesRepository(BaseRepository[Calificacion]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Calificacion)

    async def get_by_materia(
        self,
        materia_id: uuid.UUID,
        tenant_id: uuid.UUID,
        entrada_padron_id: uuid.UUID | None = None,
        actividad: str | None = None,
        aprobado: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Calificacion], int]:
        query = select(Calificacion).where(
            Calificacion.tenant_id == tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.deleted_at.is_(None),
        )
        count_query = select(func.count()).select_from(Calificacion).where(
            Calificacion.tenant_id == tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.deleted_at.is_(None),
        )

        if entrada_padron_id is not None:
            query = query.where(Calificacion.entrada_padron_id == entrada_padron_id)
            count_query = count_query.where(Calificacion.entrada_padron_id == entrada_padron_id)
        if actividad is not None:
            query = query.where(Calificacion.actividad == actividad)
            count_query = count_query.where(Calificacion.actividad == actividad)
        if aprobado is not None:
            query = query.where(Calificacion.aprobado == aprobado)
            count_query = count_query.where(Calificacion.aprobado == aprobado)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(offset).limit(limit).order_by(Calificacion.created_at.desc())
        result = await self.session.execute(query)
        calificaciones = list(result.scalars().all())

        return calificaciones, total

    async def get_by_entrada_y_actividad(
        self,
        entrada_padron_id: uuid.UUID,
        actividad: str,
        tenant_id: uuid.UUID,
    ) -> Calificacion | None:
        query = select(Calificacion).where(
            Calificacion.tenant_id == tenant_id,
            Calificacion.entrada_padron_id == entrada_padron_id,
            Calificacion.actividad == actividad,
            Calificacion.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def bulk_insert(
        self,
        calificaciones_data: list[dict],
        tenant_id: uuid.UUID,
        importado_por: uuid.UUID | None = None,
    ) -> list[Calificacion]:
        calificaciones = []
        now = datetime.now(timezone.utc)
        for data in calificaciones_data:
            c = Calificacion(
                tenant_id=tenant_id,
                entrada_padron_id=data["entrada_padron_id"],
                materia_id=data["materia_id"],
                actividad=data["actividad"],
                nota_numerica=data.get("nota_numerica"),
                nota_textual=data.get("nota_textual"),
                aprobado=data["aprobado"],
                origen=CalificacionOrigen.IMPORTADO.value,
                importado_por=importado_por,
                importado_at=now,
            )
            self.session.add(c)
            calificaciones.append(c)
        return calificaciones

    async def vaciar_datos_usuario(
        self,
        materia_id: uuid.UUID,
        usuario_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> int:
        stmt = (
            delete(Calificacion)
            .where(
                Calificacion.tenant_id == tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.importado_por == usuario_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount
