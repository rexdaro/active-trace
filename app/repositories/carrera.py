from app.repositories.base import BaseRepository
from app.models.carrera import Carrera
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class CarreraRepository(BaseRepository[Carrera]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Carrera)
        
    async def create(self, carrera: Carrera) -> Carrera:
        self.session.add(carrera)
        await self.session.commit()
        await self.session.refresh(carrera)
        return carrera
    
    async def get(self, carrera_id: uuid.UUID) -> Carrera | None:
        return await self.session.get(Carrera, carrera_id)
