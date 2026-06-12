import pytest
import pytest_asyncio
import uuid
import os
from datetime import date, datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, EstadoInstancia
from app.models.guardia import Guardia, EstadoGuardia
from app.models.audit import AuditLog
from app.models.rbac import Role
from app.services.encuentros import EncuentrosService, GuardiasService
from app.schemas.encuentro import (
    RecurrenteRequest, RecurrenteResponse,
    InstanciaEncuentroCreate, InstanciaEncuentroUpdate,
    GuardiaCreate, GuardiaUpdate,
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
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="teacher@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
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
async def test_materia2(db_session, test_tenant):
    materia = Materia(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Física",
        code="FIS101",
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
async def test_role_profesor(db_session):
    role = Role(name="PROFESOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def test_role_tutor(db_session):
    role = Role(name="TUTOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def test_role_coordinador(db_session):
    role = Role(name="COORDINADOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def test_asignacion(db_session, test_tenant, test_materia, mock_user, test_role_profesor):
    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=mock_user.id,
        role_id=test_role_profesor.id,
        contexto_id=test_materia.id,
        desde=datetime.now(timezone.utc),
    )
    db_session.add(asignacion)
    await db_session.commit()
    return asignacion


@pytest_asyncio.fixture
async def test_asignacion_tutor(db_session, test_tenant, test_materia, mock_user, test_role_tutor):
    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=mock_user.id,
        role_id=test_role_tutor.id,
        contexto_id=test_materia.id,
        desde=datetime.now(timezone.utc),
    )
    db_session.add(asignacion)
    await db_session.commit()
    return asignacion


# ═══════════════════════════════════════════════════════════════════════════════
# EncuentrosService
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrearRecurrente:

    @pytest.mark.asyncio
    async def test_creates_slot_and_4_instances_with_correct_dates(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        request = RecurrenteRequest(
            materia_id=test_materia.id,
            dia_semana="Lunes",
            horario="18:00–19:00",
            titulo="Clase Semanal",
            meet_url="https://meet.google.com/abc",
            fecha_inicio=date(2025, 3, 3),
            cant_semanas=4,
        )
        result = await EncuentrosService.crear_recurrente(db_session, request, mock_user)

        assert result.instancias_count == 4
        assert result.slot.materia_id == test_materia.id
        assert result.slot.titulo == "Clase Semanal"
        assert result.slot.cant_semanas == 4

        from sqlalchemy import select
        stmt = select(InstanciaEncuentro).where(
            InstanciaEncuentro.slot_id == result.slot.id,
        )
        rows = (await db_session.execute(stmt)).scalars().all()
        assert len(rows) == 4

        expected_dates = [
            date(2025, 3, 3),
            date(2025, 3, 10),
            date(2025, 3, 17),
            date(2025, 3, 24),
        ]
        got_dates = [r.fecha for r in rows]
        assert got_dates == expected_dates

        for r in rows:
            assert r.hora == "18:00"
            assert r.titulo == "Clase Semanal"

    @pytest.mark.asyncio
    async def test_creates_audit_log(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        request = RecurrenteRequest(
            materia_id=test_materia.id,
            dia_semana="Lunes",
            horario="18:00–19:00",
            titulo="Clase Semanal",
            fecha_inicio=date(2025, 3, 3),
            cant_semanas=2,
        )
        await EncuentrosService.crear_recurrente(db_session, request, mock_user)

        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == "ENCUENTRO_CREAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        latest = logs[-1]
        assert latest.resource == "encuentros"
        assert latest.status == "success"
        assert latest.actor_id == str(mock_user.id)
        assert latest.detalle["tipo"] == "recurrente"


class TestCrearUnico:

    @pytest.mark.asyncio
    async def test_creates_single_instance_without_slot(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        request = InstanciaEncuentroCreate(
            materia_id=test_materia.id,
            fecha=date(2025, 4, 1),
            hora="20:00",
            titulo="Clase Única",
            meet_url="https://meet.google.com/xyz",
        )
        result = await EncuentrosService.crear_unico(db_session, request, mock_user)

        assert result.id is not None
        assert result.slot_id is None
        assert result.materia_id == test_materia.id
        assert result.fecha == date(2025, 4, 1)
        assert result.hora == "20:00"
        assert result.titulo == "Clase Única"
        assert result.meet_url == "https://meet.google.com/xyz"
        assert result.estado == EstadoInstancia.PROGRAMADO.value

    @pytest.mark.asyncio
    async def test_creates_audit_log(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        request = InstanciaEncuentroCreate(
            materia_id=test_materia.id,
            fecha=date(2025, 4, 1),
            hora="20:00",
            titulo="Clase Única",
        )
        await EncuentrosService.crear_unico(db_session, request, mock_user)

        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == "ENCUENTRO_CREAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        latest = logs[-1]
        assert latest.detalle["tipo"] == "unico"


class TestEditarInstancia:

    @pytest.mark.asyncio
    async def test_rn14_changing_one_instance_does_not_affect_others(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        i1 = await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="C1", tenant_id=test_tenant.id,
        )
        i2 = await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 10),
            hora="18:00", titulo="C2", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        update = InstanciaEncuentroUpdate(estado=EstadoInstancia.REALIZADO.value)
        await EncuentrosService.editar_instancia(db_session, i1.id, update, mock_user)

        from sqlalchemy import select
        stmt = select(InstanciaEncuentro).where(InstanciaEncuentro.id == i2.id)
        i2_refresh = (await db_session.execute(stmt)).scalar_one()
        assert i2_refresh.estado == EstadoInstancia.PROGRAMADO.value

    @pytest.mark.asyncio
    async def test_updates_video_url_meet_url_and_comentario(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        instancia = await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="C1", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        update = InstanciaEncuentroUpdate(
            video_url="https://youtu.be/demo",
            meet_url="https://meet.google.com/nuevo",
            comentario="Se grabó la clase",
        )
        result = await EncuentrosService.editar_instancia(db_session, instancia.id, update, mock_user)

        assert result.video_url == "https://youtu.be/demo"
        assert result.meet_url == "https://meet.google.com/nuevo"
        assert result.comentario == "Se grabó la clase"

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_instance(
        self, db_session, test_tenant, mock_user,
    ):
        from fastapi import HTTPException
        update = InstanciaEncuentroUpdate(estado=EstadoInstancia.REALIZADO.value)
        with pytest.raises(HTTPException) as exc:
            await EncuentrosService.editar_instancia(db_session, uuid.uuid4(), update, mock_user)
        assert exc.value.status_code == 404


class TestGetInstanciasByMateria:

    @pytest.mark.asyncio
    async def test_returns_instances_for_materia(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="C1", tenant_id=test_tenant.id,
        )
        await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 10),
            hora="18:00", titulo="C2", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        result = await EncuentrosService.get_instancias_by_materia(
            db_session, test_materia.id, mock_user,
        )
        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].titulo in ("C1", "C2")

    @pytest.mark.asyncio
    async def test_filters_by_estado(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        i1 = await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="C1", tenant_id=test_tenant.id,
        )
        await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 10),
            hora="18:00", titulo="C2", tenant_id=test_tenant.id,
        )
        i1.estado = EstadoInstancia.REALIZADO.value
        await db_session.commit()

        result = await EncuentrosService.get_instancias_by_materia(
            db_session, test_materia.id, mock_user,
            estado=EstadoInstancia.PROGRAMADO.value,
        )
        assert result.total == 1
        assert result.items[0].titulo == "C2"


class TestGetAllInstancias:

    @pytest.mark.asyncio
    async def test_returns_all_instances_in_tenant(
        self, db_session, test_tenant, test_materia, test_materia2, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="C1", tenant_id=test_tenant.id,
        )
        await repo.create(
            materia_id=test_materia2.id, fecha=date(2025, 3, 5),
            hora="18:00", titulo="C2", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        result = await EncuentrosService.get_all_instancias(db_session, mock_user)
        assert result.total == 2
        assert len(result.items) == 2


class TestGenerateHtmlBlock:

    @pytest.mark.asyncio
    async def test_returns_html_with_table_structure(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, fecha=date.today() + timedelta(days=1),
            hora="18:00", titulo="Próxima Clase",
            meet_url="https://meet.google.com/abc",
            tenant_id=test_tenant.id,
        )
        await repo.create(
            materia_id=test_materia.id, fecha=date.today() + timedelta(days=8),
            hora="18:00", titulo="Siguiente Clase",
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        result = await EncuentrosService.generate_html_block(db_session, test_materia.id, mock_user)

        assert "Próxima Clase" in result.html
        assert "Siguiente Clase" in result.html
        assert "<table" in result.html
        assert "18:00" in result.html
        assert "https://meet.google.com/abc" in result.html

    @pytest.mark.asyncio
    async def test_does_not_include_past_instances(
        self, db_session, test_tenant, test_materia, mock_user,
    ):
        from app.repositories.encuentros import InstanciaEncuentroRepository
        repo = InstanciaEncuentroRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, fecha=date.today() - timedelta(days=1),
            hora="18:00", titulo="Clase Pasada",
            tenant_id=test_tenant.id,
        )
        await repo.create(
            materia_id=test_materia.id, fecha=date.today() + timedelta(days=1),
            hora="18:00", titulo="Clase Futura",
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        result = await EncuentrosService.generate_html_block(db_session, test_materia.id, mock_user)

        assert "Clase Pasada" not in result.html
        assert "Clase Futura" in result.html


# ═══════════════════════════════════════════════════════════════════════════════
# GuardiasService
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistrarGuardia:

    @pytest.mark.asyncio
    async def test_creates_guardia_with_users_asignacion(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user, test_asignacion_tutor,
    ):
        request = GuardiaCreate(
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Lunes",
            horario="18:00",
            comentarios="Primera guardia",
        )
        result = await GuardiasService.registrar(db_session, request, mock_user)

        assert result.id is not None
        assert result.materia_id == test_materia.id
        assert result.carrera_id == test_carrera.id
        assert result.cohorte_id == test_cohorte.id
        assert result.dia == "Lunes"
        assert result.horario == "18:00"
        assert result.comentarios == "Primera guardia"
        assert result.estado == EstadoGuardia.PENDIENTE.value

    @pytest.mark.asyncio
    async def test_raises_404_when_no_active_asignacion(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user,
    ):
        from fastapi import HTTPException
        request = GuardiaCreate(
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Lunes",
            horario="18:00",
        )
        with pytest.raises(HTTPException) as exc:
            await GuardiasService.registrar(db_session, request, mock_user)
        assert exc.value.status_code == 404


class TestListarGuardias:

    @pytest.mark.asyncio
    async def test_tutor_sees_own_guardias(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user, test_role_tutor, test_asignacion_tutor,
    ):
        from app.models.user_role import UserRole
        ur = UserRole(user_id=mock_user.id, role_id=test_role_tutor.id)
        db_session.add(ur)
        await db_session.commit()

        from app.repositories.guardias import GuardiaRepository
        repo = GuardiaRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion_tutor.id,
        )

        otro_user = User(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            email="other@test.com", hashed_password="h", is_2fa_enabled=False,
        )
        db_session.add(otro_user)
        await db_session.commit()

        otra_asig = Asignacion(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            user_id=otro_user.id, role_id=test_asignacion_tutor.role_id,
            contexto_id=test_materia.id,
            desde=datetime.now(timezone.utc),
        )
        db_session.add(otra_asig)
        await db_session.commit()

        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Martes", horario="14:00",
            tenant_id=test_tenant.id, asignacion_id=otra_asig.id,
        )
        await db_session.commit()

        result = await GuardiasService.listar(db_session, mock_user)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_coordinador_sees_all_guardias(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user, test_role_coordinador,
    ):
        from app.models.user_role import UserRole
        ur = UserRole(user_id=mock_user.id, role_id=test_role_coordinador.id)
        db_session.add(ur)
        await db_session.commit()

        from app.repositories.guardias import GuardiaRepository
        repo = GuardiaRepository(db_session)
        asig1 = Asignacion(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            user_id=mock_user.id, role_id=test_role_coordinador.id,
            contexto_id=test_materia.id,
            desde=datetime.now(timezone.utc),
        )
        db_session.add(asig1)
        await db_session.commit()

        otro_user = User(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            email="other@test.com", hashed_password="h", is_2fa_enabled=False,
        )
        db_session.add(otro_user)
        otra_asig = Asignacion(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            user_id=otro_user.id, role_id=test_role_coordinador.id,
            contexto_id=test_materia.id,
            desde=datetime.now(timezone.utc),
        )
        db_session.add(otra_asig)
        await db_session.commit()

        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=asig1.id,
        )
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Martes", horario="14:00",
            tenant_id=test_tenant.id, asignacion_id=otra_asig.id,
        )
        await db_session.commit()

        result = await GuardiasService.listar(db_session, mock_user)
        assert result.total == 2


class TestActualizarGuardia:

    @pytest.mark.asyncio
    async def test_updates_estado(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user, test_asignacion_tutor,
    ):
        from app.repositories.guardias import GuardiaRepository
        repo = GuardiaRepository(db_session)
        guardia = await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion_tutor.id,
        )
        await db_session.commit()

        update = GuardiaUpdate(estado=EstadoGuardia.REALIZADA.value)
        result = await GuardiasService.actualizar(db_session, guardia.id, update, mock_user)

        assert result.estado == EstadoGuardia.REALIZADA.value

    @pytest.mark.asyncio
    async def test_updates_comentarios(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user, test_asignacion_tutor,
    ):
        from app.repositories.guardias import GuardiaRepository
        repo = GuardiaRepository(db_session)
        guardia = await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion_tutor.id,
        )
        await db_session.commit()

        update = GuardiaUpdate(comentarios="Nuevo comentario")
        result = await GuardiasService.actualizar(db_session, guardia.id, update, mock_user)

        assert result.comentarios == "Nuevo comentario"

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_guardia(
        self, db_session, test_tenant, mock_user,
    ):
        from fastapi import HTTPException
        update = GuardiaUpdate(estado=EstadoGuardia.REALIZADA.value)
        with pytest.raises(HTTPException) as exc:
            await GuardiasService.actualizar(db_session, uuid.uuid4(), update, mock_user)
        assert exc.value.status_code == 404


class TestExportarCsv:

    @pytest.mark.asyncio
    async def test_returns_csv_string_with_headers(
        self, db_session, test_tenant, test_materia, test_carrera,
        test_cohorte, mock_user, test_asignacion_tutor,
    ):
        from app.repositories.guardias import GuardiaRepository
        repo = GuardiaRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion_tutor.id,
        )
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Martes", horario="14:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion_tutor.id,
        )
        await db_session.commit()

        csv_result = await GuardiasService.exportar_csv(db_session, mock_user)

        assert "dia" in csv_result
        assert "horario" in csv_result
        assert "estado" in csv_result
        assert "materia_id" in csv_result
        assert "Lunes" in csv_result
        assert "Martes" in csv_result
        assert "18:00" in csv_result
        assert "14:00" in csv_result
