import pytest
import pytest_asyncio
import uuid
import os
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, EstadoInstancia
from app.models.guardia import Guardia, EstadoGuardia
from app.repositories.encuentros import SlotEncuentroRepository, InstanciaEncuentroRepository
from app.repositories.guardias import GuardiaRepository

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
async def test_role(db_session):
    from app.models.rbac import Role
    role = Role(name="PROFESOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def test_asignacion(db_session, test_tenant, test_materia, mock_user, test_role):
    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=mock_user.id,
        role_id=test_role.id,
        contexto_id=test_materia.id,
        desde=datetime.now(timezone.utc),
    )
    db_session.add(asignacion)
    await db_session.commit()
    return asignacion


# ═══════════════════════════════════════════════════════════════════════════════
# SlotEncuentroRepository
# ═══════════════════════════════════════════════════════════════════════════════

class TestSlotEncuentroRepository:

    @pytest.mark.asyncio
    async def test_create_slot(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        slot = await repo.create_slot(
            materia_id=test_materia.id,
            creado_por=mock_user.id,
            dia_semana="Lunes",
            horario="18:00",
            titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1),
            cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()
        assert slot.id is not None
        assert slot.materia_id == test_materia.id
        assert slot.creado_por == mock_user.id
        assert slot.dia_semana == "Lunes"
        assert slot.horario == "18:00"
        assert slot.titulo == "Clase 1"
        assert slot.fecha_inicio == date(2025, 3, 1)
        assert slot.cant_semanas == 16
        assert slot.activo is True
        assert slot.tenant_id == test_tenant.id
        assert slot.meet_url is None

    @pytest.mark.asyncio
    async def test_create_slot_with_meet_url(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        slot = await repo.create_slot(
            materia_id=test_materia.id,
            creado_por=mock_user.id,
            dia_semana="Miércoles",
            horario="18:00",
            titulo="Clase 2",
            meet_url="https://meet.google.com/abc",
            fecha_inicio=date(2025, 3, 3),
            cant_semanas=8,
            tenant_id=test_tenant.id,
        )
        assert slot.meet_url == "https://meet.google.com/abc"
        assert slot.cant_semanas == 8

    @pytest.mark.asyncio
    async def test_get_by_materia(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        s1 = await repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        s2 = await repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Miércoles", horario="18:00", titulo="Clase 2",
            fecha_inicio=date(2025, 3, 3), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        otra_materia_id = uuid.uuid4()
        await repo.create_slot(
            materia_id=otra_materia_id, creado_por=mock_user.id,
            dia_semana="Viernes", horario="18:00", titulo="Otra",
            fecha_inicio=date(2025, 3, 5), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        slots = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=test_tenant.id,
        )
        assert len(slots) == 2
        ids = {s.id for s in slots}
        assert s1.id in ids
        assert s2.id in ids

    @pytest.mark.asyncio
    async def test_get_by_materia_aislado_por_tenant(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        await repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        slots = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=otro_tenant_id,
        )
        assert len(slots) == 0

    @pytest.mark.asyncio
    async def test_get_activo_returns_slot(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        slot = await repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        result = await repo.get_activo(
            slot_id=slot.id, tenant_id=test_tenant.id,
        )
        assert result is not None
        assert result.id == slot.id
        assert result.activo is True

    @pytest.mark.asyncio
    async def test_get_activo_returns_none_when_inactive(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        slot = await repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=16,
            tenant_id=test_tenant.id, activo=False,
        )
        await db_session.commit()

        result = await repo.get_activo(
            slot_id=slot.id, tenant_id=test_tenant.id,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_activo_returns_none_for_wrong_tenant(self, db_session, test_tenant, test_materia, mock_user):
        repo = SlotEncuentroRepository(db_session)
        slot = await repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        result = await repo.get_activo(
            slot_id=slot.id, tenant_id=otro_tenant_id,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_activo_returns_none_for_missing(self, db_session, test_tenant):
        repo = SlotEncuentroRepository(db_session)
        result = await repo.get_activo(
            slot_id=uuid.uuid4(), tenant_id=test_tenant.id,
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# InstanciaEncuentroRepository
# ═══════════════════════════════════════════════════════════════════════════════

class TestInstanciaEncuentroRepository:

    @pytest.mark.asyncio
    async def test_create(self, db_session, test_tenant, test_materia):
        repo = InstanciaEncuentroRepository(db_session)
        instancia = await repo.create(
            materia_id=test_materia.id,
            fecha=date(2025, 3, 3),
            hora="18:00",
            titulo="Clase 1",
            tenant_id=test_tenant.id,
        )
        await db_session.commit()
        assert instancia.id is not None
        assert instancia.materia_id == test_materia.id
        assert instancia.fecha == date(2025, 3, 3)
        assert instancia.hora == "18:00"
        assert instancia.titulo == "Clase 1"
        assert instancia.estado == EstadoInstancia.PROGRAMADO.value
        assert instancia.slot_id is None
        assert instancia.meet_url is None
        assert instancia.video_url is None
        assert instancia.comentario is None
        assert instancia.tenant_id == test_tenant.id

    @pytest.mark.asyncio
    async def test_create_with_slot_and_meet(self, db_session, test_tenant, test_materia, mock_user):
        slot_repo = SlotEncuentroRepository(db_session)
        slot = await slot_repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=16,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()
        inst_repo = InstanciaEncuentroRepository(db_session)
        instancia = await inst_repo.create(
            slot_id=slot.id,
            materia_id=test_materia.id,
            fecha=date(2025, 3, 3),
            hora="18:00",
            titulo="Clase 1",
            meet_url="https://meet.google.com/abc",
            tenant_id=test_tenant.id,
        )
        assert instancia.slot_id == slot.id
        assert instancia.meet_url == "https://meet.google.com/abc"

    @pytest.mark.asyncio
    async def test_bulk_create(self, db_session, test_tenant, test_materia):
        repo = InstanciaEncuentroRepository(db_session)
        instances_data = [
            {"materia_id": test_materia.id, "fecha": date(2025, 3, 3), "hora": "18:00",
             "titulo": "Clase 1", "tenant_id": test_tenant.id},
            {"materia_id": test_materia.id, "fecha": date(2025, 3, 10), "hora": "18:00",
             "titulo": "Clase 2", "tenant_id": test_tenant.id},
            {"materia_id": test_materia.id, "fecha": date(2025, 3, 17), "hora": "18:00",
             "titulo": "Clase 3", "tenant_id": test_tenant.id},
        ]
        instancias = await repo.bulk_create(instances_data)
        await db_session.commit()

        assert len(instancias) == 3
        for inst in instancias:
            assert inst.id is not None
            assert inst.estado == EstadoInstancia.PROGRAMADO.value

    @pytest.mark.asyncio
    async def test_bulk_create_with_slot(self, db_session, test_tenant, test_materia, mock_user):
        slot_repo = SlotEncuentroRepository(db_session)
        slot = await slot_repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=3,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()
        inst_repo = InstanciaEncuentroRepository(db_session)
        instances_data = [
            {"slot_id": slot.id, "materia_id": test_materia.id, "fecha": date(2025, 3, 3),
             "hora": "18:00", "titulo": "Clase 1", "tenant_id": test_tenant.id},
            {"slot_id": slot.id, "materia_id": test_materia.id, "fecha": date(2025, 3, 10),
             "hora": "18:00", "titulo": "Clase 2", "tenant_id": test_tenant.id},
        ]
        instancias = await inst_repo.bulk_create(instances_data)
        await db_session.commit()

        assert len(instancias) == 2
        for inst in instancias:
            assert inst.slot_id == slot.id

    @pytest.mark.asyncio
    async def test_get_by_materia(self, db_session, test_tenant, test_materia):
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

        instancias, total = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=test_tenant.id,
        )
        assert total == 2
        assert len(instancias) == 2

    @pytest.mark.asyncio
    async def test_get_by_materia_aislado_por_tenant(self, db_session, test_tenant, test_materia):
        repo = InstanciaEncuentroRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="C1", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        instancias, total = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=otro_tenant_id,
        )
        assert total == 0
        assert len(instancias) == 0

    @pytest.mark.asyncio
    async def test_get_by_materia_filters_estado(self, db_session, test_tenant, test_materia):
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

        instancias, total = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=test_tenant.id,
            estado=EstadoInstancia.PROGRAMADO.value,
        )
        assert total == 1
        assert instancias[0].titulo == "C2"

    @pytest.mark.asyncio
    async def test_get_by_materia_pagination(self, db_session, test_tenant, test_materia):
        repo = InstanciaEncuentroRepository(db_session)
        for i in range(5):
            await repo.create(
                materia_id=test_materia.id, fecha=date(2025, 3, 3 + i * 7),
                hora="18:00", titulo=f"C{i + 1}", tenant_id=test_tenant.id,
            )
        await db_session.commit()

        page, total = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=test_tenant.id,
            offset=0, limit=3,
        )
        assert total == 5
        assert len(page) == 3

        page2, total2 = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=test_tenant.id,
            offset=3, limit=3,
        )
        assert total2 == 5
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_get_by_slot(self, db_session, test_tenant, test_materia, mock_user):
        slot_repo = SlotEncuentroRepository(db_session)
        slot = await slot_repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Clase 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=4,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()
        inst_repo = InstanciaEncuentroRepository(db_session)
        i1 = await inst_repo.create(
            slot_id=slot.id, materia_id=test_materia.id,
            fecha=date(2025, 3, 3), hora="18:00", titulo="C1",
            tenant_id=test_tenant.id,
        )
        i2 = await inst_repo.create(
            slot_id=slot.id, materia_id=test_materia.id,
            fecha=date(2025, 3, 10), hora="18:00", titulo="C2",
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        instancias = await inst_repo.get_by_slot(
            slot_id=slot.id, tenant_id=test_tenant.id,
        )
        assert len(instancias) == 2
        ids = {i.id for i in instancias}
        assert i1.id in ids
        assert i2.id in ids

    @pytest.mark.asyncio
    async def test_get_by_slot_excludes_other_slots(self, db_session, test_tenant, test_materia, mock_user):
        slot_repo = SlotEncuentroRepository(db_session)
        slot1 = await slot_repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Lunes", horario="18:00", titulo="Slot 1",
            fecha_inicio=date(2025, 3, 1), cant_semanas=4,
            tenant_id=test_tenant.id,
        )
        slot2 = await slot_repo.create_slot(
            materia_id=test_materia.id, creado_por=mock_user.id,
            dia_semana="Miércoles", horario="18:00", titulo="Slot 2",
            fecha_inicio=date(2025, 3, 3), cant_semanas=4,
            tenant_id=test_tenant.id,
        )
        await db_session.commit()
        inst_repo = InstanciaEncuentroRepository(db_session)
        await inst_repo.create(
            slot_id=slot1.id, materia_id=test_materia.id,
            fecha=date(2025, 3, 3), hora="18:00", titulo="C1",
            tenant_id=test_tenant.id,
        )
        await inst_repo.create(
            slot_id=slot2.id, materia_id=test_materia.id,
            fecha=date(2025, 3, 5), hora="18:00", titulo="C2",
            tenant_id=test_tenant.id,
        )
        await db_session.commit()

        slot1_instancias = await inst_repo.get_by_slot(
            slot_id=slot1.id, tenant_id=test_tenant.id,
        )
        assert len(slot1_instancias) == 1
        assert slot1_instancias[0].titulo == "C1"

    @pytest.mark.asyncio
    async def test_update_instancia_cambia_estado(self, db_session, test_tenant, test_materia):
        repo = InstanciaEncuentroRepository(db_session)
        instancia = await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="Clase 1", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        updated = await repo.update_instancia(
            id=instancia.id,
            data={
                "estado": EstadoInstancia.REALIZADO.value,
                "comentario": "Se dictó normal",
            },
            tenant_id=test_tenant.id,
        )
        assert updated is not None
        assert updated.estado == EstadoInstancia.REALIZADO.value
        assert updated.comentario == "Se dictó normal"

    @pytest.mark.asyncio
    async def test_update_instancia_no_afecta_otras_rn14(self, db_session, test_tenant, test_materia):
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

        await repo.update_instancia(
            id=i1.id,
            data={"estado": EstadoInstancia.REALIZADO.value},
            tenant_id=test_tenant.id,
        )

        todas, total = await repo.get_by_materia(
            materia_id=test_materia.id, tenant_id=test_tenant.id,
        )
        i2_actual = [i for i in todas if i.id == i2.id][0]
        assert i2_actual.estado == EstadoInstancia.PROGRAMADO.value

    @pytest.mark.asyncio
    async def test_update_instancia_video_url(self, db_session, test_tenant, test_materia):
        repo = InstanciaEncuentroRepository(db_session)
        instancia = await repo.create(
            materia_id=test_materia.id, fecha=date(2025, 3, 3),
            hora="18:00", titulo="Clase 1", tenant_id=test_tenant.id,
        )
        await db_session.commit()

        updated = await repo.update_instancia(
            id=instancia.id,
            data={"video_url": "https://youtu.be/abc"},
            tenant_id=test_tenant.id,
        )
        assert updated.video_url == "https://youtu.be/abc"

    @pytest.mark.asyncio
    async def test_update_instancia_not_found(self, db_session, test_tenant):
        repo = InstanciaEncuentroRepository(db_session)
        result = await repo.update_instancia(
            id=uuid.uuid4(),
            data={"estado": EstadoInstancia.REALIZADO.value},
            tenant_id=test_tenant.id,
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# GuardiaRepository
# ═══════════════════════════════════════════════════════════════════════════════

class TestGuardiaRepository:

    @pytest.mark.asyncio
    async def test_create(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        guardia = await repo.create(
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Lunes",
            horario="18:00",
            tenant_id=test_tenant.id,
            asignacion_id=test_asignacion.id,
        )
        await db_session.commit()
        assert guardia.id is not None
        assert guardia.materia_id == test_materia.id
        assert guardia.carrera_id == test_carrera.id
        assert guardia.cohorte_id == test_cohorte.id
        assert guardia.dia == "Lunes"
        assert guardia.horario == "18:00"
        assert guardia.estado == EstadoGuardia.PENDIENTE.value
        assert guardia.comentarios is None
        assert guardia.asignacion_id == test_asignacion.id
        assert guardia.tenant_id == test_tenant.id

    @pytest.mark.asyncio
    async def test_create_with_comentarios(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        guardia = await repo.create(
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Martes",
            horario="14:00",
            comentarios="Posible cambio de horario",
            tenant_id=test_tenant.id,
            asignacion_id=test_asignacion.id,
        )
        assert guardia.comentarios == "Posible cambio de horario"

    @pytest.mark.asyncio
    async def test_get_by_user(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, mock_user, test_role,
        test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        g1 = await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )

        otro_user = User(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            email="other@test.com", hashed_password="h",
            is_2fa_enabled=False,
        )
        db_session.add(otro_user)
        await db_session.commit()

        otra_asig = Asignacion(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            user_id=otro_user.id, role_id=test_role.id,
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

        guardias, total = await repo.get_by_user(
            user_id=mock_user.id, tenant_id=test_tenant.id,
        )
        assert total == 1
        assert guardias[0].id == g1.id

        guardias_otro, total_otro = await repo.get_by_user(
            user_id=otro_user.id, tenant_id=test_tenant.id,
        )
        assert total_otro == 1

    @pytest.mark.asyncio
    async def test_get_by_user_filter_by_materia(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, mock_user, test_role,
        test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )

        otra_materia = Materia(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            name="Física", code="FIS101", is_active=True,
        )
        db_session.add(otra_materia)
        await db_session.commit()

        otra_asig = Asignacion(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            user_id=mock_user.id, role_id=test_role.id,
            contexto_id=otra_materia.id,
            desde=datetime.now(timezone.utc),
        )
        db_session.add(otra_asig)
        await db_session.commit()

        await repo.create(
            materia_id=otra_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Martes", horario="14:00",
            tenant_id=test_tenant.id, asignacion_id=otra_asig.id,
        )
        await db_session.commit()

        guardias, total = await repo.get_by_user(
            user_id=mock_user.id, tenant_id=test_tenant.id,
            materia_id=test_materia.id,
        )
        assert total == 1
        assert guardias[0].materia_id == test_materia.id

    @pytest.mark.asyncio
    async def test_get_by_user_pagination(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, mock_user, test_role,
        test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        extra_asigs = []
        for i in range(5):
            asig = Asignacion(
                id=uuid.uuid4(), tenant_id=test_tenant.id,
                user_id=mock_user.id, role_id=test_role.id,
                contexto_id=test_materia.id,
                desde=datetime.now(timezone.utc),
            )
            db_session.add(asig)
            extra_asigs.append(asig)
        await db_session.commit()

        for i, asig in enumerate(extra_asigs):
            await repo.create(
                materia_id=test_materia.id, carrera_id=test_carrera.id,
                cohorte_id=test_cohorte.id,
                dia="Lunes" if i % 2 == 0 else "Martes",
                horario=f"{14 + i}:00",
                tenant_id=test_tenant.id, asignacion_id=asig.id,
            )
        await db_session.commit()

        page, total = await repo.get_by_user(
            user_id=mock_user.id, tenant_id=test_tenant.id,
            offset=0, limit=3,
        )
        assert total >= 5  # podrían haber más de test_asignacion también
        assert len(page) == 3

    @pytest.mark.asyncio
    async def test_get_all(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Martes", horario="14:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )
        await db_session.commit()

        guardias, total = await repo.get_all(tenant_id=test_tenant.id)
        assert total == 2
        assert len(guardias) == 2

    @pytest.mark.asyncio
    async def test_get_all_aislado_por_tenant(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        guardias, total = await repo.get_all(tenant_id=otro_tenant_id)
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_all_filter_by_materia(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )

        otra_materia = Materia(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            name="Física", code="FIS101", is_active=True,
        )
        db_session.add(otra_materia)
        await db_session.commit()

        await repo.create(
            materia_id=otra_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Martes", horario="14:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )
        await db_session.commit()

        guardias, total = await repo.get_all(
            tenant_id=test_tenant.id, materia_id=test_materia.id,
        )
        assert total == 1
        assert guardias[0].materia_id == test_materia.id

    @pytest.mark.asyncio
    async def test_update_guardia(
        self, db_session, test_tenant, test_materia,
        test_carrera, test_cohorte, test_asignacion,
    ):
        repo = GuardiaRepository(db_session)
        guardia = await repo.create(
            materia_id=test_materia.id, carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id, dia="Lunes", horario="18:00",
            tenant_id=test_tenant.id, asignacion_id=test_asignacion.id,
        )
        await db_session.commit()

        updated = await repo.update_guardia(
            id=guardia.id,
            data={
                "estado": EstadoGuardia.REALIZADA.value,
                "comentarios": "Completada",
            },
            tenant_id=test_tenant.id,
        )
        assert updated is not None
        assert updated.estado == EstadoGuardia.REALIZADA.value
        assert updated.comentarios == "Completada"

    @pytest.mark.asyncio
    async def test_update_guardia_not_found(self, db_session, test_tenant):
        repo = GuardiaRepository(db_session)
        result = await repo.update_guardia(
            id=uuid.uuid4(),
            data={"estado": EstadoGuardia.REALIZADA.value},
            tenant_id=test_tenant.id,
        )
        assert result is None
