import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.umbral_materia import UmbralMateria
from app.models.asignacion import Asignacion


class UmbralMateriaRepository(BaseRepository[UmbralMateria]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UmbralMateria)

    async def get_by_asignacion_y_materia(
        self,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> UmbralMateria | None:
        query = select(UmbralMateria).where(
            UmbralMateria.tenant_id == tenant_id,
            UmbralMateria.asignacion_id == asignacion_id,
            UmbralMateria.materia_id == materia_id,
            UmbralMateria.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        tenant_id: uuid.UUID,
        umbral_pct: int | None = None,
        valores_aprobatorios: list[str] | None = None,
    ) -> UmbralMateria:
        existing = await self.get_by_asignacion_y_materia(asignacion_id, materia_id, tenant_id)

        if existing:
            if umbral_pct is not None:
                existing.umbral_pct = umbral_pct
            if valores_aprobatorios is not None:
                existing.valores_aprobatorios = valores_aprobatorios
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        umbral = UmbralMateria(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct or 60,
            valores_aprobatorios=valores_aprobatorios or ["Satisfactorio", "Supera lo esperado"],
        )
        self.session.add(umbral)
        await self.session.commit()
        await self.session.refresh(umbral)
        return umbral

    @staticmethod
    async def get_asignacion_id(
        db: AsyncSession,
        user_id: uuid.UUID,
        materia_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> uuid.UUID | None:
        query = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.user_id == user_id,
            Asignacion.contexto_id == materia_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await db.execute(query)
        asignacion = result.scalar_one_or_none()
        return asignacion.id if asignacion else None
