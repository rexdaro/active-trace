import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.fechas_academicas import FechaAcademicaRepository
from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.user import User
from app.schemas.fecha_academica import (
    FechaAcademicaCreate,
    FechaAcademicaUpdate,
    FechaAcademicaListParams,
)


class FechaAcademicaService:

    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: FechaAcademicaCreate,
        usuario_actual: User,
    ) -> FechaAcademica:
        materia = await db.get(Materia, obj_in.materia_id)
        if not materia:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")

        cohorte = await db.get(Cohorte, obj_in.cohorte_id)
        if not cohorte:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")

        repo = FechaAcademicaRepository(db)
        data = obj_in.model_dump()
        data["tipo"] = obj_in.tipo.value if hasattr(obj_in.tipo, "value") else obj_in.tipo
        fecha = await repo.create(data, usuario_actual.tenant_id)
        await db.commit()
        await db.refresh(fecha)
        return fecha

    @staticmethod
    async def get(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> FechaAcademica:
        repo = FechaAcademicaRepository(db)
        fecha = await repo.get(id, usuario_actual.tenant_id)
        if not fecha:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")
        return fecha

    @staticmethod
    async def update(
        db: AsyncSession,
        id: uuid.UUID,
        obj_in: FechaAcademicaUpdate,
        usuario_actual: User,
    ) -> FechaAcademica:
        repo = FechaAcademicaRepository(db)
        fecha = await repo.get(id, usuario_actual.tenant_id)
        if not fecha:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")

        data = obj_in.model_dump(exclude_unset=True)
        if "tipo" in data and data["tipo"] is not None:
            data["tipo"] = data["tipo"].value if hasattr(data["tipo"], "value") else data["tipo"]
        updated = await repo.update(fecha, data)
        await db.commit()
        await db.refresh(updated)
        return updated

    @staticmethod
    async def delete(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> None:
        repo = FechaAcademicaRepository(db)
        fecha = await repo.get(id, usuario_actual.tenant_id)
        if not fecha:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")

        await repo.delete(id, usuario_actual.tenant_id)
        await db.commit()

    @staticmethod
    async def list(
        db: AsyncSession,
        usuario_actual: User,
        params: FechaAcademicaListParams | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[FechaAcademica], int]:
        repo = FechaAcademicaRepository(db)
        return await repo.list(
            tenant_id=usuario_actual.tenant_id,
            params=params,
            offset=offset,
            limit=limit,
        )

    @staticmethod
    async def generate_html(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> str:
        repo = FechaAcademicaRepository(db)
        fecha = await repo.get(id, usuario_actual.tenant_id)
        if not fecha:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")

        fechas = await repo.list_html(
            tenant_id=usuario_actual.tenant_id,
            materia_id=fecha.materia_id,
            cohorte_id=fecha.cohorte_id,
        )

        rows = "\n".join(
            f"<tr><td>{f.titulo}</td><td>{f.tipo}</td><td>{f.numero}</td>"
            f"<td>{f.periodo}</td><td>{f.fecha.isoformat()}</td></tr>"
            for f in fechas
        )
        return (
            f"<table>\n<thead><tr><th>Título</th><th>Tipo</th><th>N°</th>"
            f"<th>Período</th><th>Fecha</th></tr></thead>\n<tbody>\n{rows}\n</tbody>\n</table>"
        )
