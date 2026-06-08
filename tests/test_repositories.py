import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column
from app.repositories.base import BaseRepository
from app.models.base import Base

# Dummy model for testing
class TenantAwareModel(Base):
    __tablename__ = "tenant_aware_model"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column()
    data: Mapped[str] = mapped_column()

# Setup in-memory DB for tests
@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest.mark.asyncio
async def test_base_repository_filters_by_tenant(db_session):
    repo = BaseRepository(db_session, TenantAwareModel)
    
    tenant1 = uuid.uuid4()
    tenant2 = uuid.uuid4()
    
    # Add data for both tenants
    obj1 = TenantAwareModel(tenant_id=tenant1, data="data1")
    obj2 = TenantAwareModel(tenant_id=tenant2, data="data2")
    
    db_session.add(obj1)
    db_session.add(obj2)
    await db_session.commit()
    
    # Query for tenant1
    results = await repo.get_all(tenant_id=tenant1)
    
    assert len(results) == 1
    assert results[0].data == "data1"

@pytest.mark.asyncio
async def test_base_repository_filters_by_tenant_triangulation(db_session):
    repo = BaseRepository(db_session, TenantAwareModel)
    
    tenant1 = uuid.uuid4()
    tenant2 = uuid.uuid4()
    
    # Add data for both tenants
    obj1 = TenantAwareModel(tenant_id=tenant1, data="data1")
    obj2 = TenantAwareModel(tenant_id=tenant2, data="data2")
    
    db_session.add(obj1)
    db_session.add(obj2)
    await db_session.commit()
    
    # Query for tenant1
    results1 = await repo.get_all(tenant_id=tenant1)
    assert len(results1) == 1
    assert results1[0].data == "data1"
    
    # Query for tenant2
    results2 = await repo.get_all(tenant_id=tenant2)
    assert len(results2) == 1
    assert results2[0].data == "data2"
