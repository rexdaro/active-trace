import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.user import Usuario
from app.models.coloquio import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, TipoEvaluacion, EstadoReserva


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


@pytest_asyncio.fixture
async def test_user(db_session, test_tenant):
    user = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        _email="alumno@test.com",
        _dni="12345678",
        _cuil="20-12345678-9",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_evaluacion(db_session, test_tenant, test_materia, test_cohorte):
    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        materia_id=test_materia.id,
        cohorte_id=test_cohorte.id,
        tipo=TipoEvaluacion.PARCIAL.value,
        instancia="1er Parcial",
    )
    db_session.add(evaluacion)
    await db_session.commit()
    return evaluacion


class TestEvaluacionModel:

    @pytest.mark.asyncio
    async def test_create_evaluacion(self, db_session, test_tenant, test_materia, test_cohorte):
        evaluacion = Evaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoEvaluacion.PARCIAL.value,
            instancia="1er Parcial",
        )
        db_session.add(evaluacion)
        await db_session.commit()

        assert evaluacion.cupos_por_dia == 10
        assert evaluacion.tipo == TipoEvaluacion.PARCIAL.value
        assert evaluacion.instancia == "1er Parcial"

    @pytest.mark.asyncio
    async def test_tipo_evaluacion_enum(self):
        assert TipoEvaluacion.PARCIAL.value == "Parcial"
        assert TipoEvaluacion.TP.value == "TP"
        assert TipoEvaluacion.COLOQUIO.value == "Coloquio"
        assert TipoEvaluacion.RECUPERATORIO.value == "Recuperatorio"

    @pytest.mark.asyncio
    async def test_cupos_por_dia_default(self, db_session, test_tenant, test_materia, test_cohorte):
        evaluacion = Evaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoEvaluacion.TP.value,
            instancia="TP 1",
        )
        db_session.add(evaluacion)
        await db_session.commit()

        assert evaluacion.cupos_por_dia == 10


class TestReservaEvaluacionModel:

    @pytest.mark.asyncio
    async def test_create_reserva(self, db_session, test_tenant, test_evaluacion, test_user):
        reserva = ReservaEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            fecha_hora=datetime(2026, 6, 15, 10, 0),
        )
        db_session.add(reserva)
        await db_session.commit()

        assert reserva.estado == EstadoReserva.ACTIVA.value
        assert reserva.fecha_hora == datetime(2026, 6, 15, 10, 0)

    @pytest.mark.asyncio
    async def test_cancelar_reserva(self, db_session, test_tenant, test_evaluacion, test_user):
        reserva = ReservaEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            fecha_hora=datetime(2026, 6, 15, 10, 0),
        )
        db_session.add(reserva)
        await db_session.commit()

        reserva.estado = EstadoReserva.CANCELADA.value
        await db_session.commit()
        await db_session.refresh(reserva)

        assert reserva.estado == EstadoReserva.CANCELADA.value

    @pytest.mark.asyncio
    async def test_reserva_unique_constraint(self, db_session, test_tenant, test_evaluacion, test_user):
        reserva1 = ReservaEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            fecha_hora=datetime(2026, 6, 15, 10, 0),
        )
        db_session.add(reserva1)
        await db_session.commit()

        reserva2 = ReservaEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            fecha_hora=datetime(2026, 6, 16, 10, 0),
        )
        db_session.add(reserva2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_estado_reserva_enum(self):
        assert EstadoReserva.ACTIVA.value == "Activa"
        assert EstadoReserva.CANCELADA.value == "Cancelada"


class TestResultadoEvaluacionModel:

    @pytest.mark.asyncio
    async def test_create_resultado(self, db_session, test_tenant, test_evaluacion, test_user):
        resultado = ResultadoEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            nota_final="8",
        )
        db_session.add(resultado)
        await db_session.commit()

        assert resultado.nota_final == "8"

    @pytest.mark.asyncio
    async def test_resultado_unique_constraint(self, db_session, test_tenant, test_evaluacion, test_user):
        resultado1 = ResultadoEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            nota_final="7",
        )
        db_session.add(resultado1)
        await db_session.commit()

        resultado2 = ResultadoEvaluacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            evaluacion_id=test_evaluacion.id,
            alumno_id=test_user.id,
            nota_final="8",
        )
        db_session.add(resultado2)

        with pytest.raises(Exception):
            await db_session.commit()
