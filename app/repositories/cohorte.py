from app.repositories.base import BaseRepository
from app.models.cohorte import Cohorte
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class CohorteRepository(BaseRepository[Cohorte]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Cohorte)
        
    async def create(self, cohorte: Cohorte) -> Cohorte:
        self.session.add(cohorte)
        await self.session.commit()
        await self.session.refresh(cohorte)
        return cohorte
