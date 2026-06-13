import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.programa_materia import ProgramaMateria
from app.repositories.programas_materia import ProgramaMateriaRepository
from app.schemas.programa_materia import ProgramaMateriaListParams


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
async def otro_tenant(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Otro Tenant")
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


@pytest_asyncio.fixture
async def repo(db_session):
    return ProgramaMateriaRepository(db_session)


@pytest.mark.asyncio
class TestProgramaMateriaRepo:

    async def test_create(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "Programa 2026",
        }
        programa = await repo.create(data, test_tenant.id)
        await db_session.commit()

        assert programa.id is not None
        assert programa.titulo == "Programa 2026"
        assert programa.tenant_id == test_tenant.id
        assert programa.materia_id == test_materia.id

    async def test_get(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "Get test",
        }
        programa = await repo.create(data, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get(programa.id, test_tenant.id)
        assert fetched is not None
        assert fetched.titulo == "Get test"

    async def test_get_not_found(self, repo, db_session, test_tenant):
        fetched = await repo.get(uuid.uuid4(), test_tenant.id)
        assert fetched is None

    async def test_update(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "Original",
        }
        programa = await repo.create(data, test_tenant.id)
        await db_session.commit()

        updated = await repo.update(programa, {"titulo": "Modificado", "referencia_archivo": "v2.pdf"})
        await db_session.commit()

        assert updated.titulo == "Modificado"
        assert updated.referencia_archivo == "v2.pdf"

        fetched = await repo.get(programa.id, test_tenant.id)
        assert fetched.titulo == "Modificado"

    async def test_delete_soft(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "A eliminar",
        }
        programa = await repo.create(data, test_tenant.id)
        await db_session.commit()

        await repo.delete(programa.id, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get(programa.id, test_tenant.id)
        assert fetched is None

    async def test_list_with_filters(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        otra_materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Física", code="FIS101")
        db_session.add(otra_materia)
        await db_session.commit()

        data1 = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "Matematica",
        }
        data2 = {
            "materia_id": otra_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "Fisica",
        }
        await repo.create(data1, test_tenant.id)
        await repo.create(data2, test_tenant.id)
        await db_session.commit()

        params = ProgramaMateriaListParams(materia_id=test_materia.id)
        items, total = await repo.list(test_tenant.id, params)
        assert total == 1
        assert items[0].titulo == "Matematica"

    async def test_list_all(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        for i in range(3):
            data = {
                "materia_id": test_materia.id,
                "carrera_id": test_carrera.id,
                "cohorte_id": test_cohorte.id,
                "titulo": f"Programa {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(test_tenant.id)
        assert total == 3
        assert len(items) == 3

    async def test_pagination(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        for i in range(5):
            data = {
                "materia_id": test_materia.id,
                "carrera_id": test_carrera.id,
                "cohorte_id": test_cohorte.id,
                "titulo": f"Programa {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(test_tenant.id, offset=0, limit=2)
        assert total == 5
        assert len(items) == 2

    async def test_tenant_isolation(self, repo, db_session, test_tenant, otro_tenant, test_materia, test_carrera, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "Solo tenant 1",
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(otro_tenant.id)
        assert total == 0
        assert len(items) == 0

    async def test_soft_deleted_hidden_from_list(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "carrera_id": test_carrera.id,
            "cohorte_id": test_cohorte.id,
            "titulo": "A ocultar",
        }
        programa = await repo.create(data, test_tenant.id)
        await db_session.commit()

        await repo.delete(programa.id, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(test_tenant.id)
        assert total == 0

    async def test_count(self, repo, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        for i in range(3):
            data = {
                "materia_id": test_materia.id,
                "carrera_id": test_carrera.id,
                "cohorte_id": test_cohorte.id,
                "titulo": f"Programa {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        count = await repo.count(test_tenant.id)
        assert count == 3
