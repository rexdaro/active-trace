import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.programa_materia import ProgramaMateria
from sqlalchemy.sql import func


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_tenant(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db_session.add(tenant)
    await db_session.commit()
    return tenant


@pytest_asyncio.fixture
async def test_materia(db_session, test_tenant):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="MAT101")
    db_session.add(materia)
    await db_session.commit()
    return materia


@pytest_asyncio.fixture
async def test_carrera(db_session, test_tenant):
    carrera = Carrera(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Ing. Sistemas", code="IS")
    db_session.add(carrera)
    await db_session.commit()
    return carrera


@pytest_asyncio.fixture
async def test_cohorte(db_session, test_tenant, test_carrera):
    cohorte = Cohorte(id=uuid.uuid4(), tenant_id=test_tenant.id, carrera_id=test_carrera.id, name="2026")
    db_session.add(cohorte)
    await db_session.commit()
    return cohorte


class TestProgramaMateriaModel:

    @pytest.mark.asyncio
    async def test_create_programa_defaults(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Programa 2026",
        )
        db_session.add(programa)
        await db_session.commit()

        assert programa.titulo == "Programa 2026"
        assert programa.referencia_archivo is None
        assert programa.materia_id == test_materia.id
        assert programa.carrera_id == test_carrera.id
        assert programa.cohorte_id == test_cohorte.id

    @pytest.mark.asyncio
    async def test_create_programa_with_all_fields(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Programa 2026",
            referencia_archivo="uploads/programa_v1.pdf",
        )
        db_session.add(programa)
        await db_session.commit()

        assert programa.referencia_archivo == "uploads/programa_v1.pdf"

    @pytest.mark.asyncio
    async def test_fk_materia(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Test FK",
        )
        db_session.add(programa)
        await db_session.commit()

        fetched = await db_session.get(Materia, test_materia.id)
        assert fetched is not None

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="A eliminar",
        )
        db_session.add(programa)
        await db_session.commit()

        programa.deleted_at = datetime(2026, 6, 13)
        await db_session.commit()

        query = select(ProgramaMateria).where(
            ProgramaMateria.id == programa.id,
            ProgramaMateria.deleted_at.is_(None),
        )
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        otro_tenant = Tenant(id=uuid.uuid4(), name="Otro Tenant")
        db_session.add(otro_tenant)
        await db_session.commit()

        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Mi programa",
        )
        db_session.add(programa)
        await db_session.commit()

        query = select(ProgramaMateria).where(
            ProgramaMateria.id == programa.id,
            ProgramaMateria.tenant_id == otro_tenant.id,
        )
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cargado_at_default(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Con cargado_at",
        )
        db_session.add(programa)
        await db_session.commit()

        assert programa.cargado_at is not None
