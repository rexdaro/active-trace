import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column
from app.repositories.base import BaseRepository
from app.models.base import Base
from app.models.tenant import Tenant

# Model to test isolation
class TenantData(Base):
    __tablename__ = "tenant_data"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column()
    content: Mapped[str] = mapped_column()

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
async def test_tenant_data_isolation(db_session):
    # 1. Create Tenant A and Tenant B
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    
    db_session.add(tenant_a)
    db_session.add(tenant_b)
    await db_session.commit()
    
    # 2. Add data for Tenant A
    data_a = TenantData(tenant_id=tenant_a.id, content="Secret A")
    db_session.add(data_a)
    
    # 3. Add data for Tenant B
    data_b = TenantData(tenant_id=tenant_b.id, content="Secret B")
    db_session.add(data_b)
    
    await db_session.commit()
    
    # 4. Verify Tenant A cannot query Tenant B's data
    repo = BaseRepository(db_session, TenantData)
    
    results_a = await repo.get_all(tenant_id=tenant_a.id)
    assert len(results_a) == 1
    assert results_a[0].content == "Secret A"
    assert results_a[0].tenant_id == tenant_a.id
    
    results_b = await repo.get_all(tenant_id=tenant_b.id)
    assert len(results_b) == 1
    assert results_b[0].content == "Secret B"
    assert results_b[0].tenant_id == tenant_b.id
    
    # Verify Tenant A doesn't see B's data
    for item in results_a:
        assert item.content != "Secret B"
        assert item.tenant_id != tenant_b.id
