import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.user import Usuario
from app.models.coloquio import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, EstadoReserva
from app.repositories.coloquios import ColoquiosRepository
from app.core.security import encrypt

_ENCRYPTION_KEY = "test-key-32-chars-long-for-encryption!!"
os.environ["ENCRYPTION_KEY"] = _ENCRYPTION_KEY


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
    materia = Materia(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Matemática",
        code="MAT101",
        is_active=True,
    )
    db_session.add(materia)
    await db_session.commit()
    return materia


@pytest_asyncio.fixture
async def test_carrera(db_session, test_tenant):
    carrera = Carrera(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Ingeniería",
        code="ING",
        is_active=True,
    )
    db_session.add(carrera)
    await db_session.commit()
    return carrera


@pytest_asyncio.fixture
async def test_cohorte(db_session, test_tenant, test_carrera):
    cohorte = Cohorte(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        carrera_id=test_carrera.id,
        name="2025",
        is_active=True,
    )
    db_session.add(cohorte)
    await db_session.commit()
    return cohorte


@pytest_asyncio.fixture
async def test_alumno(db_session, test_tenant):
    alumno = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        _email=encrypt("alumno@test.com", _ENCRYPTION_KEY),
        _dni=encrypt("12345678", _ENCRYPTION_KEY),
        _cuil=encrypt("20-12345678-9", _ENCRYPTION_KEY),
        _cbu=None,
    )
    db_session.add(alumno)
    await db_session.commit()
    return alumno


@pytest_asyncio.fixture
async def repo(db_session):
    return ColoquiosRepository(db_session)


@pytest.mark.asyncio
class TestEvaluacion:

    async def test_crear_y_get_evaluacion(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": "Parcial",
            "instancia": "2025-06-01",
            "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()
        assert ev.id is not None
        assert ev.materia_id == test_materia.id
        assert ev.cohorte_id == test_cohorte.id
        assert ev.tipo == "Parcial"
        assert ev.instancia == "2025-06-01"
        assert ev.cupos_por_dia == 10
        assert ev.tenant_id == test_tenant.id

        fetched = await repo.get_evaluacion(ev.id, test_tenant.id)
        assert fetched is not None
        assert fetched.id == ev.id
        assert fetched.tipo == "Parcial"

    async def test_get_evaluacion_not_found(self, repo, test_tenant):
        fetched = await repo.get_evaluacion(uuid.uuid4(), test_tenant.id)
        assert fetched is None

    async def test_get_evaluacion_wrong_tenant(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id,
            "cohorte_id": test_cohorte.id,
            "tipo": "TP",
            "instancia": "Primera",
            "cupos_por_dia": 5,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()
        otro_tenant_id = uuid.uuid4()
        fetched = await repo.get_evaluacion(ev.id, otro_tenant_id)
        assert fetched is None

    async def test_get_evaluaciones_pagination(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        for i in range(5):
            await repo.crear_evaluacion({
                "materia_id": test_materia.id,
                "cohorte_id": test_cohorte.id,
                "tipo": "Parcial",
                "instancia": f"Instancia {i+1}",
                "cupos_por_dia": 10,
                "tenant_id": test_tenant.id,
            })
        await db_session.commit()

        items, total = await repo.get_evaluaciones(test_tenant.id, offset=0, limit=3)
        assert total == 5
        assert len(items) == 3

        items2, total2 = await repo.get_evaluaciones(test_tenant.id, offset=3, limit=3)
        assert total2 == 5
        assert len(items2) == 2

    async def test_get_evaluaciones_filter_by_materia(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        otra_materia = Materia(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            name="Física", code="FIS101", is_active=True,
        )
        db_session.add(otra_materia)
        await db_session.commit()

        await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await repo.crear_evaluacion({
            "materia_id": otra_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "TP", "instancia": "1", "cupos_por_dia": 5,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        items, total = await repo.get_evaluaciones(
            test_tenant.id, materia_id=test_materia.id,
        )
        assert total == 1
        assert items[0].materia_id == test_materia.id

    async def test_get_evaluaciones_aislado_por_tenant(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        items, total = await repo.get_evaluaciones(otro_tenant_id)
        assert total == 0
        assert len(items) == 0

    async def test_get_evaluaciones_activas(self, repo, db_session, test_tenant, test_materia, test_cohorte):
        await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        activas = await repo.get_evaluaciones_activas(test_tenant.id)
        assert len(activas) >= 1


@pytest.mark.asyncio
class TestReserva:

    async def test_crear_y_get_reserva(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        res = await repo.crear_reserva({
            "evaluacion_id": ev.id,
            "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()
        assert res.id is not None
        assert res.evaluacion_id == ev.id
        assert res.alumno_id == test_alumno.id
        assert res.estado == EstadoReserva.ACTIVA.value

        fetched = await repo.get_reserva(res.id, test_tenant.id)
        assert fetched is not None
        assert fetched.id == res.id

    async def test_get_reserva_not_found(self, repo, test_tenant):
        fetched = await repo.get_reserva(uuid.uuid4(), test_tenant.id)
        assert fetched is None

    async def test_get_reserva_wrong_tenant(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()
        res = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        fetched = await repo.get_reserva(res.id, uuid.uuid4())
        assert fetched is None

    async def test_get_reservas_by_evaluacion(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        otro_alumno = Usuario(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            _email=encrypt("otro@test.com", _ENCRYPTION_KEY),
            _dni=encrypt("87654321", _ENCRYPTION_KEY),
            _cuil=encrypt("20-87654321-9", _ENCRYPTION_KEY),
        )
        db_session.add(otro_alumno)
        await db_session.commit()

        r1 = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        r2 = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": otro_alumno.id,
            "fecha_hora": datetime(2025, 6, 11, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        reservas = await repo.get_reservas_by_evaluacion(ev.id, test_tenant.id)
        assert len(reservas) == 2
        ids = {r.id for r in reservas}
        assert r1.id in ids
        assert r2.id in ids

    async def test_get_reservas_by_evaluacion_filter_estado(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        r1 = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        await repo.cancelar_reserva(r1.id, test_tenant.id)
        await db_session.commit()

        activas = await repo.get_reservas_by_evaluacion(
            ev.id, test_tenant.id, estado=EstadoReserva.ACTIVA.value,
        )
        assert len(activas) == 0

        canceladas = await repo.get_reservas_by_evaluacion(
            ev.id, test_tenant.id, estado=EstadoReserva.CANCELADA.value,
        )
        assert len(canceladas) == 1

    async def test_get_reservas_by_alumno(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev1 = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        ev2 = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "TP", "instancia": "1", "cupos_por_dia": 5,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        r1 = await repo.crear_reserva({
            "evaluacion_id": ev1.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        r2 = await repo.crear_reserva({
            "evaluacion_id": ev2.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 12, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        reservas = await repo.get_reservas_by_alumno(test_alumno.id, test_tenant.id)
        assert len(reservas) == 2
        ids = {r.id for r in reservas}
        assert r1.id in ids
        assert r2.id in ids

    async def test_get_reservas_activas_by_alumno(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        r1 = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        activas = await repo.get_reservas_activas_by_alumno(
            test_alumno.id, ev.id, test_tenant.id,
        )
        assert len(activas) == 1
        assert activas[0].id == r1.id

        await repo.cancelar_reserva(r1.id, test_tenant.id)
        await db_session.commit()

        activas = await repo.get_reservas_activas_by_alumno(
            test_alumno.id, ev.id, test_tenant.id,
        )
        assert len(activas) == 0

    async def test_cancelar_reserva(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        res = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        cancelled = await repo.cancelar_reserva(res.id, test_tenant.id)
        assert cancelled is not None
        assert cancelled.estado == EstadoReserva.CANCELADA.value

    async def test_cancelar_reserva_wrong_tenant(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()
        res = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        cancelled = await repo.cancelar_reserva(res.id, uuid.uuid4())
        assert cancelled is None

    async def test_cancelar_reserva_not_found(self, repo, test_tenant):
        cancelled = await repo.cancelar_reserva(uuid.uuid4(), test_tenant.id)
        assert cancelled is None

    async def test_count_reservas_activas_by_evaluacion_y_fecha(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 3,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        fecha = datetime(2025, 6, 10, 14, 0, 0)

        for i in range(3):
            alumno = Usuario(
                id=uuid.uuid4(), tenant_id=test_tenant.id,
                _email=encrypt(f"alumno{i}@test.com", _ENCRYPTION_KEY),
                _dni=encrypt(f"{i}"*8, _ENCRYPTION_KEY),
                _cuil=encrypt(f"20-{i}235678-9", _ENCRYPTION_KEY),
            )
            db_session.add(alumno)
            await db_session.commit()
            await repo.crear_reserva({
                "evaluacion_id": ev.id, "alumno_id": alumno.id,
                "fecha_hora": fecha, "tenant_id": test_tenant.id,
            })
        await db_session.commit()

        count = await repo.count_reservas_activas_by_evaluacion_y_fecha(
            ev.id, fecha, test_tenant.id,
        )
        assert count == 3

    async def test_count_reservas_ignores_other_fechas(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        fecha1 = datetime(2025, 6, 10, 14, 0, 0)
        fecha2 = datetime(2025, 6, 11, 14, 0, 0)

        await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": fecha1, "tenant_id": test_tenant.id,
        })
        otro = Usuario(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            _email=encrypt("otro@test.com", _ENCRYPTION_KEY),
            _dni=encrypt("87654321", _ENCRYPTION_KEY),
            _cuil=encrypt("20-87654321-9", _ENCRYPTION_KEY),
        )
        db_session.add(otro)
        await db_session.commit()
        await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": otro.id,
            "fecha_hora": fecha2, "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        count1 = await repo.count_reservas_activas_by_evaluacion_y_fecha(
            ev.id, fecha1, test_tenant.id,
        )
        assert count1 == 1

        count2 = await repo.count_reservas_activas_by_evaluacion_y_fecha(
            ev.id, fecha2, test_tenant.id,
        )
        assert count2 == 1

    async def test_count_reservas_ignores_canceladas(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        fecha = datetime(2025, 6, 10, 14, 0, 0)

        res = await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": fecha, "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        await repo.cancelar_reserva(res.id, test_tenant.id)
        await db_session.commit()

        count = await repo.count_reservas_activas_by_evaluacion_y_fecha(
            ev.id, fecha, test_tenant.id,
        )
        assert count == 0


@pytest.mark.asyncio
class TestResultado:

    async def test_crear_y_get_resultados_by_evaluacion(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        res = await repo.crear_resultado({
            "evaluacion_id": ev.id,
            "alumno_id": test_alumno.id,
            "nota_final": "Aprobado",
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()
        assert res.id is not None
        assert res.evaluacion_id == ev.id
        assert res.alumno_id == test_alumno.id
        assert res.nota_final == "Aprobado"

        resultados = await repo.get_resultados_by_evaluacion(ev.id, test_tenant.id)
        assert len(resultados) == 1
        assert resultados[0].id == res.id

    async def test_get_resultados_by_evaluacion_empty(self, repo, test_tenant):
        resultados = await repo.get_resultados_by_evaluacion(uuid.uuid4(), test_tenant.id)
        assert resultados == []


@pytest.mark.asyncio
class TestPanelMetricas:

    async def test_empty(self, repo, test_tenant):
        metrics = await repo.get_panel_metricas(test_tenant.id)
        assert metrics.total_evaluaciones == 0
        assert metrics.total_reservas_activas == 0
        assert metrics.total_resultados == 0
        assert metrics.total_alumnos_convocados == 0

    async def test_with_data(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        await repo.crear_resultado({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "nota_final": "8", "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        metrics = await repo.get_panel_metricas(test_tenant.id)
        assert metrics.total_evaluaciones == 1
        assert metrics.total_reservas_activas == 1
        assert metrics.total_resultados == 1
        assert metrics.total_alumnos_convocados == 1

    async def test_aislado_por_tenant(self, repo, db_session, test_tenant, test_materia, test_cohorte, test_alumno):
        ev = await repo.crear_evaluacion({
            "materia_id": test_materia.id, "cohorte_id": test_cohorte.id,
            "tipo": "Parcial", "instancia": "1", "cupos_por_dia": 10,
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        await repo.crear_reserva({
            "evaluacion_id": ev.id, "alumno_id": test_alumno.id,
            "fecha_hora": datetime(2025, 6, 10, 14, 0, 0),
            "tenant_id": test_tenant.id,
        })
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        metrics = await repo.get_panel_metricas(otro_tenant_id)
        assert metrics.total_evaluaciones == 0
        assert metrics.total_reservas_activas == 0
        assert metrics.total_resultados == 0
        assert metrics.total_alumnos_convocados == 0
