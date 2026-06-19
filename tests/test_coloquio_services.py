import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.coloquio import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, EstadoReserva
from app.models.audit import AuditLog
from app.services.coloquios import ColoquiosService
from app.schemas.coloquio import (
    EvaluacionCreate, ReservaCreate, ResultadoCreate,
    ImportAlumnosRequest, ImportAlumnosResponse,
    ReservaCancelResponse,
)

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"


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
async def mock_user(db_session, test_tenant):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=test_tenant.id,
        email="alumno@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
        dni="0",
        cuil="0",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def mock_coordinador(db_session, test_tenant):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=test_tenant.id,
        email="coord@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
        dni="0",
        cuil="0",
    )
    db_session.add(user)
    await db_session.commit()
    return user


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
async def test_evaluacion(db_session, test_tenant, test_materia, test_cohorte):
    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        materia_id=test_materia.id,
        cohorte_id=test_cohorte.id,
        tipo="Parcial",
        instancia="Primer Parcial",
        cupos_por_dia=5,
    )
    db_session.add(evaluacion)
    await db_session.commit()
    return evaluacion


@pytest_asyncio.fixture
async def otro_alumno(db_session, test_tenant):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=test_tenant.id,
        email="otro@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
        dni="0",
        cuil="0",
    )
    db_session.add(user)
    await db_session.commit()
    return user


# ═══════════════════════════════════════════════════════════════════════════════
# Convocatoria
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrearConvocatoria:

    @pytest.mark.asyncio
    async def test_creates_evaluacion_and_audit(
        self, db_session, test_tenant, test_materia, test_cohorte, mock_coordinador,
    ):
        request = EvaluacionCreate(
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo="Parcial",
            instancia="Primer Parcial",
            cupos_por_dia=10,
        )
        result = await ColoquiosService.crear_convocatoria(db_session, request, mock_coordinador)

        assert result.id is not None
        assert result.materia_id == test_materia.id
        assert result.cohorte_id == test_cohorte.id
        assert result.tipo == "Parcial"
        assert result.instancia == "Primer Parcial"
        assert result.cupos_por_dia == 10

        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == "COLOQUIO_CREAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        latest = logs[-1]
        assert latest.resource == "coloquios"
        assert latest.status == "success"
        assert latest.actor_id == str(mock_coordinador.id)


class TestGetConvocatorias:

    @pytest.mark.asyncio
    async def test_returns_list_with_metrics(
        self, db_session, test_tenant, test_materia, test_cohorte,
        test_evaluacion, mock_coordinador,
    ):
        result = await ColoquiosService.get_convocatorias(db_session, mock_coordinador)

        assert result.total >= 1
        assert len(result.items) >= 1
        item = result.items[0]
        assert item.id == test_evaluacion.id
        assert item.tipo == "Parcial"
        assert item.reservas_activas == 0


class TestGetPanelMetricas:

    @pytest.mark.asyncio
    async def test_returns_correct_counts(
        self, db_session, test_tenant, test_materia, test_cohorte,
        test_evaluacion, mock_coordinador,
    ):
        result = await ColoquiosService.get_panel_metricas(db_session, mock_coordinador)

        assert result.total_evaluaciones >= 1
        assert result.total_reservas_activas == 0
        assert result.total_resultados == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Reserva (FL-07)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReservarTurno:

    @pytest.mark.asyncio
    async def test_reservar_con_cupo_disponible(
        self, db_session, test_tenant, test_evaluacion, mock_user,
    ):
        request = ReservaCreate(
            evaluacion_id=test_evaluacion.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
        )
        result = await ColoquiosService.reservar_turno(db_session, request, mock_user)

        assert result.id is not None
        assert result.evaluacion_id == test_evaluacion.id
        assert result.alumno_id == mock_user.id
        assert result.estado == EstadoReserva.ACTIVA.value

        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == "COLOQUIO_RESERVAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1

    @pytest.mark.asyncio
    async def test_reservar_sin_cupo_returns_400(
        self, db_session, test_tenant, test_evaluacion, mock_user, otro_alumno,
    ):
        from fastapi import HTTPException

        evaluacion = test_evaluacion
        evaluacion.cupos_por_dia = 1
        await db_session.commit()

        # First alumno reserves — fills the single cupo
        otra_reserva = ReservaEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            alumno_id=otro_alumno.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
            estado=EstadoReserva.ACTIVA.value,
            tenant_id=test_tenant.id,
        )
        db_session.add(otra_reserva)
        await db_session.commit()

        request = ReservaCreate(
            evaluacion_id=evaluacion.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await ColoquiosService.reservar_turno(db_session, request, mock_user)
        assert exc.value.status_code == 400
        assert "cupos" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_reservar_duplicado_returns_400(
        self, db_session, test_tenant, test_evaluacion, mock_user,
    ):
        from fastapi import HTTPException

        # Create first reservation for mock_user
        existing = ReservaEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=mock_user.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
            estado=EstadoReserva.ACTIVA.value,
            tenant_id=test_tenant.id,
        )
        db_session.add(existing)
        await db_session.commit()

        request = ReservaCreate(
            evaluacion_id=test_evaluacion.id,
            fecha_hora=datetime(2025, 6, 16, 10, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await ColoquiosService.reservar_turno(db_session, request, mock_user)
        assert exc.value.status_code == 400
        assert "reserva activa" in exc.value.detail.lower()


class TestCancelarReserva:

    @pytest.mark.asyncio
    async def test_cancelar_reserva_frees_cupo(
        self, db_session, test_tenant, test_evaluacion, mock_user, otro_alumno,
    ):
        test_evaluacion.cupos_por_dia = 1
        await db_session.commit()

        # mock_user fills the single cupo
        reserva = ReservaEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=mock_user.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
            estado=EstadoReserva.ACTIVA.value,
            tenant_id=test_tenant.id,
        )
        db_session.add(reserva)
        await db_session.commit()

        # Cancel — frees the cupo
        result = await ColoquiosService.cancelar_reserva(db_session, reserva.id, mock_user)
        assert result.estado == EstadoReserva.CANCELADA.value

        # Now otro_alumno can reserve the same slot (cupo freed)
        request = ReservaCreate(
            evaluacion_id=test_evaluacion.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
        )
        new_reserva = await ColoquiosService.reservar_turno(db_session, request, otro_alumno)
        assert new_reserva.id is not None
        assert new_reserva.estado == EstadoReserva.ACTIVA.value

    @pytest.mark.asyncio
    async def test_cancelar_reserva_ya_cancelada_returns_400(
        self, db_session, test_tenant, test_evaluacion, mock_user,
    ):
        from fastapi import HTTPException

        reserva = ReservaEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=mock_user.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
            estado=EstadoReserva.CANCELADA.value,
            tenant_id=test_tenant.id,
        )
        db_session.add(reserva)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await ColoquiosService.cancelar_reserva(db_session, reserva.id, mock_user)
        assert exc.value.status_code == 400
        assert "activas" in exc.value.detail.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Import (F7.2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestImportAlumnos:

    @pytest.mark.asyncio
    async def test_import_returns_count_and_audit(
        self, db_session, test_tenant, test_evaluacion, mock_coordinador,
    ):
        alumno_ids = []
        for _ in range(3):
            u = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"imp_{uuid.uuid4()}@t.com", hashed_password="x", dni="0", cuil="0")
            db_session.add(u)
            alumno_ids.append(u.id)
        await db_session.flush()
        request = ImportAlumnosRequest(
            evaluacion_id=test_evaluacion.id,
            alumno_ids=alumno_ids,
        )
        result = await ColoquiosService.import_alumnos(db_session, request, mock_coordinador)

        assert result.evaluacion_id == test_evaluacion.id
        assert result.cantidad == 3

        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == "COLOQUIO_IMPORTAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        assert logs[-1].detalle["cantidad"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Resultados
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistrarResultado:

    @pytest.mark.asyncio
    async def test_creates_resultado_and_audit(
        self, db_session, test_tenant, test_evaluacion, mock_coordinador,
    ):
        alumno = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"res_{uuid.uuid4()}@t.com", hashed_password="x", dni="0", cuil="0")
        db_session.add(alumno)
        await db_session.flush()
        request = ResultadoCreate(
            evaluacion_id=test_evaluacion.id,
            alumno_id=alumno.id,
            nota_final="8",
        )
        result = await ColoquiosService.registrar_resultado(db_session, request, mock_coordinador)

        assert result.id is not None
        assert result.evaluacion_id == test_evaluacion.id
        assert result.nota_final == "8"

        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == "COLOQUIO_RESULTADO")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        assert logs[-1].detalle["nota"] == "8"


class TestGetResultados:

    @pytest.mark.asyncio
    async def test_returns_list_for_evaluacion(
        self, db_session, test_tenant, test_evaluacion, mock_coordinador,
    ):
        a1 = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"rl1_{uuid.uuid4()}@t.com", hashed_password="x", dni="0", cuil="0")
        a2 = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"rl2_{uuid.uuid4()}@t.com", hashed_password="x", dni="0", cuil="0")
        db_session.add_all([a1, a2])
        await db_session.flush()
        r1 = ResultadoEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=a1.id,
            nota_final="7",
            tenant_id=test_tenant.id,
        )
        r2 = ResultadoEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=a2.id,
            nota_final="9",
            tenant_id=test_tenant.id,
        )
        db_session.add_all([r1, r2])
        await db_session.commit()

        results = await ColoquiosService.get_resultados(db_session, test_evaluacion.id, mock_coordinador)

        assert len(results) == 2
        notas = {r.nota_final for r in results}
        assert notas == {"7", "9"}


# ═══════════════════════════════════════════════════════════════════════════════
# Alumno
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetMisReservas:

    @pytest.mark.asyncio
    async def test_returns_only_that_alumnos_reservas(
        self, db_session, test_tenant, test_evaluacion, mock_user, otro_alumno,
    ):
        r1 = ReservaEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=mock_user.id,
            fecha_hora=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
            estado=EstadoReserva.ACTIVA.value,
            tenant_id=test_tenant.id,
        )
        r2 = ReservaEvaluacion(
            id=uuid.uuid4(),
            evaluacion_id=test_evaluacion.id,
            alumno_id=otro_alumno.id,
            fecha_hora=datetime(2025, 6, 16, 10, 0, tzinfo=timezone.utc),
            estado=EstadoReserva.ACTIVA.value,
            tenant_id=test_tenant.id,
        )
        db_session.add_all([r1, r2])
        await db_session.commit()

        result = await ColoquiosService.get_mis_reservas(db_session, mock_user)

        assert len(result) == 1
        assert result[0].alumno_id == mock_user.id
