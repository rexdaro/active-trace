import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.carrera import Carrera
from app.repositories.carrera import CarreraRepository

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
async def test_create_carrera(db_session):
    repo = CarreraRepository(db_session)
    tenant_id = uuid.uuid4()
    carrera = Carrera(tenant_id=tenant_id, name="Ingeniería", code="ING")
    
    created = await repo.create(carrera)
    assert created.id is not None
    assert created.name == "Ingeniería"
    assert created.code == "ING"
    assert created.tenant_id == tenant_id
