import pytest
import pytest_asyncio
import uuid
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.repositories.fechas_academicas import FechaAcademicaRepository
from app.schemas.fecha_academica import FechaAcademicaListParams


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
    return FechaAcademicaRepository(db_session)


@pytest.mark.asyncio
class TestFechaAcademicaRepo:

    async def test_create(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "1er Parcial",
        }
        fecha_obj = await repo.create(data, test_tenant.id)
        await db_session.commit()

        assert fecha_obj.id is not None
        assert fecha_obj.titulo == "1er Parcial"
        assert fecha_obj.tenant_id == test_tenant.id
        assert fecha_obj.materia_id == test_materia.id

    async def test_get(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "Get test",
        }
        fecha_obj = await repo.create(data, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get(fecha_obj.id, test_tenant.id)
        assert fetched is not None
        assert fetched.titulo == "Get test"

    async def test_get_not_found(self, repo, db_session, test_tenant):
        fetched = await repo.get(uuid.uuid4(), test_tenant.id)
        assert fetched is None

    async def test_update(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "Original",
        }
        fecha_obj = await repo.create(data, test_tenant.id)
        await db_session.commit()

        updated = await repo.update(fecha_obj, {"titulo": "Modificado", "numero": 2})
        await db_session.commit()

        assert updated.titulo == "Modificado"
        assert updated.numero == 2

        fetched = await repo.get(fecha_obj.id, test_tenant.id)
        assert fetched.titulo == "Modificado"

    async def test_delete_soft(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "A eliminar",
        }
        fecha_obj = await repo.create(data, test_tenant.id)
        await db_session.commit()

        await repo.delete(fecha_obj.id, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get(fecha_obj.id, test_tenant.id)
        assert fetched is None

    async def test_list_all(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        for i in range(3):
            data = {
                "materia_id": test_materia.id,
                "cohorte_id": test_cohorte.id,
                "tipo": TipoFecha.PARCIAL.value,
                "numero": i + 1,
                "periodo": "2026",
                "fecha": date(2026, 6, 15),
                "titulo": f"Parcial {i + 1}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(test_tenant.id)
        assert total == 3
        assert len(items) == 3

    async def test_list_with_filters(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        otra_materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Física", code="FIS101")
        db_session.add(otra_materia)
        await db_session.commit()

        data1 = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "Matematica Parcial",
        }
        data2 = {
            "materia_id": otra_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.TP.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 20),
            "titulo": "Fisica TP",
        }
        await repo.create(data1, test_tenant.id)
        await repo.create(data2, test_tenant.id)
        await db_session.commit()

        # Filter by materia
        params = FechaAcademicaListParams(materia_id=test_materia.id)
        items, total = await repo.list(test_tenant.id, params)
        assert total == 1
        assert items[0].titulo == "Matematica Parcial"

        # Filter by tipo
        params = FechaAcademicaListParams(tipo=TipoFecha.TP.value)
        items, total = await repo.list(test_tenant.id, params)
        assert total == 1
        assert items[0].titulo == "Fisica TP"

    async def test_pagination(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        for i in range(5):
            data = {
                "materia_id": test_materia.id,
                "cohorte_id": test_cohorte.id,
                "tipo": TipoFecha.PARCIAL.value,
                "numero": i + 1,
                "periodo": "2026",
                "fecha": date(2026, 6, 15),
                "titulo": f"Parcial {i + 1}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(test_tenant.id, offset=0, limit=2)
        assert total == 5
        assert len(items) == 2

    async def test_tenant_isolation(self, repo, db_session, test_tenant, otro_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "Solo tenant 1",
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(otro_tenant.id)
        assert total == 0
        assert len(items) == 0

    async def test_soft_deleted_hidden_from_list(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "A ocultar",
        }
        fecha_obj = await repo.create(data, test_tenant.id)
        await db_session.commit()

        await repo.delete(fecha_obj.id, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list(test_tenant.id)
        assert total == 0

    async def test_list_html_ordered_by_fecha(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        fechas_data = [
            {"numero": 2, "fecha": date(2026, 7, 15), "titulo": "2do Parcial"},
            {"numero": 1, "fecha": date(2026, 6, 15), "titulo": "1er Parcial"},
            {"numero": 3, "fecha": date(2026, 8, 15), "titulo": "3er Parcial"},
        ]
        for f in fechas_data:
            data = {
                "materia_id": test_materia.id,
                "cohorte_id": test_cohorte.id,
                "tipo": TipoFecha.PARCIAL.value,
                "numero": f["numero"],
                "periodo": "2026",
                "fecha": f["fecha"],
                "titulo": f["titulo"],
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        result = await repo.list_html(test_tenant.id, test_materia.id, test_cohorte.id)
        assert len(result) == 3
        assert result[0].titulo == "1er Parcial"
        assert result[1].titulo == "2do Parcial"
        assert result[2].titulo == "3er Parcial"

    async def test_list_html_excludes_soft_deleted(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        data = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 1,
            "periodo": "2026",
            "fecha": date(2026, 6, 15),
            "titulo": "Visible",
        }
        f1 = await repo.create(data, test_tenant.id)
        data2 = {
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": TipoFecha.PARCIAL.value,
            "numero": 2,
            "periodo": "2026",
            "fecha": date(2026, 7, 15),
            "titulo": "Oculto",
        }
        f2 = await repo.create(data2, test_tenant.id)
        await db_session.commit()

        await repo.delete(f2.id, test_tenant.id)
        await db_session.commit()

        result = await repo.list_html(test_tenant.id, test_materia.id, test_cohorte.id)
        assert len(result) == 1
        assert result[0].titulo == "Visible"
