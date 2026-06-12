from app.repositories.base import BaseRepository
from app.models.materia import Materia
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class MateriaRepository(BaseRepository[Materia]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Materia)
        
    async def create(self, materia: Materia) -> Materia:
        self.session.add(materia)
        await self.session.commit()
        await self.session.refresh(materia)
        return materia
