import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.programas_materia import ProgramaMateriaRepository
from app.models.programa_materia import ProgramaMateria
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.user import User
from app.schemas.programa_materia import (
    ProgramaMateriaCreate,
    ProgramaMateriaUpdate,
    ProgramaMateriaListParams,
)


class ProgramaMateriaService:

    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: ProgramaMateriaCreate,
        usuario_actual: User,
    ) -> ProgramaMateria:
        materia = await db.get(Materia, obj_in.materia_id)
        if not materia:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")

        carrera = await db.get(Carrera, obj_in.carrera_id)
        if not carrera:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")

        cohorte = await db.get(Cohorte, obj_in.cohorte_id)
        if not cohorte:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")

        repo = ProgramaMateriaRepository(db)
        data = obj_in.model_dump()
        programa = await repo.create(data, usuario_actual.tenant_id)
        await db.commit()
        await db.refresh(programa)
        return programa

    @staticmethod
    async def get(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> ProgramaMateria:
        repo = ProgramaMateriaRepository(db)
        programa = await repo.get(id, usuario_actual.tenant_id)
        if not programa:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Programa no encontrado")
        return programa

    @staticmethod
    async def update(
        db: AsyncSession,
        id: uuid.UUID,
        obj_in: ProgramaMateriaUpdate,
        usuario_actual: User,
    ) -> ProgramaMateria:
        repo = ProgramaMateriaRepository(db)
        programa = await repo.get(id, usuario_actual.tenant_id)
        if not programa:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Programa no encontrado")

        data = obj_in.model_dump(exclude_unset=True)
        updated = await repo.update(programa, data)
        await db.commit()
        await db.refresh(updated)
        return updated

    @staticmethod
    async def delete(
        db: AsyncSession,
        id: uuid.UUID,
        usuario_actual: User,
    ) -> None:
        repo = ProgramaMateriaRepository(db)
        programa = await repo.get(id, usuario_actual.tenant_id)
        if not programa:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Programa no encontrado")

        await repo.delete(id, usuario_actual.tenant_id)
        await db.commit()

    @staticmethod
    async def list(
        db: AsyncSession,
        usuario_actual: User,
        params: ProgramaMateriaListParams | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[ProgramaMateria], int]:
        repo = ProgramaMateriaRepository(db)
        return await repo.list(
            tenant_id=usuario_actual.tenant_id,
            params=params,
            offset=offset,
            limit=limit,
        )
