from typing import Generic, TypeVar, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get_all(self, tenant_id: Any) -> list[T]:
        # Filter by tenant_id
        # We assume the model has a 'tenant_id' attribute
        query = select(self.model).where(self.model.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
