import uuid
from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.padron import VersionPadron, EntradaPadron


class PadronRepository(BaseRepository[VersionPadron]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, VersionPadron)

    async def get_activa(self, materia_id: uuid.UUID, cohorte_id: uuid.UUID, tenant_id: uuid.UUID) -> VersionPadron | None:
        query = select(VersionPadron).where(
            VersionPadron.tenant_id == tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.cohorte_id == cohorte_id,
            VersionPadron.activa == True,
            VersionPadron.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def desactivar_anterior(self, materia_id: uuid.UUID, cohorte_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        stmt = (
            update(VersionPadron)
            .where(
                VersionPadron.tenant_id == tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa == True,
            )
            .values(activa=False)
        )
        await self.session.execute(stmt)

    async def crear_version(self, **kwargs) -> VersionPadron:
        version = VersionPadron(**kwargs)
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def bulk_insert_entradas(self, entradas: list[EntradaPadron]) -> None:
        self.session.add_all(entradas)

    async def vaciar_datos_usuario(self, materia_id: uuid.UUID, usuario_id: uuid.UUID, tenant_id: uuid.UUID) -> int:
        stmt = (
            delete(VersionPadron)
            .where(
                VersionPadron.tenant_id == tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cargado_por == usuario_id,
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def get_versiones_materia(self, materia_id: uuid.UUID, tenant_id: uuid.UUID) -> list[VersionPadron]:
        query = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.deleted_at.is_(None),
            )
            .order_by(VersionPadron.created_at.desc())
        )
        result = await self.session.execute(query)
        versiones = list(result.scalars().all())

        for v in versiones:
            count_query = select(func.count()).select_from(EntradaPadron).where(
                EntradaPadron.version_id == v.id,
                EntradaPadron.deleted_at.is_(None),
            )
            count_result = await self.session.execute(count_query)
            v.entradas_count = count_result.scalar() or 0

        return versiones

    async def get_version_by_hash(self, archivo_hash: str, materia_id: uuid.UUID, cohorte_id: uuid.UUID, tenant_id: uuid.UUID) -> VersionPadron | None:
        query = select(VersionPadron).where(
            VersionPadron.tenant_id == tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.cohorte_id == cohorte_id,
            VersionPadron.archivo_hash == archivo_hash,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_entradas_count(self, version_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(EntradaPadron).where(
            EntradaPadron.version_id == version_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
