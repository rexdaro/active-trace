import pytest
import pytest_asyncio
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, EstadoInstancia
from app.models.guardia import Guardia, EstadoGuardia


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


class TestSlotEncuentroModel:

    @pytest.mark.asyncio
    async def test_create_slot_recurrente(self, db_session, test_tenant, test_materia):
        slot = SlotEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            creado_por=uuid.uuid4(),
            dia_semana="Lunes",
            horario="18:00–20:00",
            titulo="Clase 1",
            fecha_inicio=date(2026, 3, 1),
            cant_semanas=16,
        )
        db_session.add(slot)
        await db_session.commit()

        assert slot.activo is True
        assert slot.dia_semana == "Lunes"
        assert slot.titulo == "Clase 1"
        assert slot.cant_semanas == 16

    @pytest.mark.asyncio
    async def test_slot_meet_url_nullable(self, db_session, test_tenant, test_materia):
        slot = SlotEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            creado_por=uuid.uuid4(),
            dia_semana="Martes",
            horario="10:00–12:00",
            titulo="Clase 2",
            fecha_inicio=date(2026, 3, 1),
            cant_semanas=16,
        )
        db_session.add(slot)
        await db_session.commit()

        assert slot.meet_url is None

    @pytest.mark.asyncio
    async def test_slot_with_meet_url(self, db_session, test_tenant, test_materia):
        slot = SlotEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            creado_por=uuid.uuid4(),
            dia_semana="Miércoles",
            horario="14:00–16:00",
            titulo="Clase 3",
            fecha_inicio=date(2026, 3, 1),
            cant_semanas=16,
            meet_url="https://meet.google.com/abc-defg-hij",
        )
        db_session.add(slot)
        await db_session.commit()

        assert slot.meet_url == "https://meet.google.com/abc-defg-hij"


class TestInstanciaEncuentroModel:

    @pytest.mark.asyncio
    async def test_create_instancia(self, db_session, test_tenant, test_materia):
        instancia = InstanciaEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            fecha=date(2026, 3, 7),
            hora="18:00",
            titulo="Clase 1 - Semana 1",
        )
        db_session.add(instancia)
        await db_session.commit()

        assert instancia.estado == EstadoInstancia.PROGRAMADO.value
        assert instancia.slot_id is None
        assert instancia.meet_url is None
        assert instancia.video_url is None
        assert instancia.comentario is None

    @pytest.mark.asyncio
    async def test_instancia_with_slot(self, db_session, test_tenant, test_materia):
        slot = SlotEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            creado_por=uuid.uuid4(),
            dia_semana="Lunes",
            horario="18:00–20:00",
            titulo="Clase 1",
            fecha_inicio=date(2026, 3, 1),
            cant_semanas=16,
        )
        db_session.add(slot)
        await db_session.commit()

        instancia = InstanciaEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            slot_id=slot.id,
            materia_id=test_materia.id,
            fecha=date(2026, 3, 7),
            hora="18:00",
            titulo="Clase 1 - Semana 1",
        )
        db_session.add(instancia)
        await db_session.commit()

        assert instancia.slot_id == slot.id

    @pytest.mark.asyncio
    async def test_instancia_estado_enum(self):
        assert EstadoInstancia.PROGRAMADO.value == "Programado"
        assert EstadoInstancia.REALIZADO.value == "Realizado"
        assert EstadoInstancia.CANCELADO.value == "Cancelado"

    @pytest.mark.asyncio
    async def test_instancia_independent_state(self, db_session, test_tenant, test_materia):
        slot = SlotEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            creado_por=uuid.uuid4(),
            dia_semana="Lunes",
            horario="18:00–20:00",
            titulo="Clase 1",
            fecha_inicio=date(2026, 3, 1),
            cant_semanas=16,
        )
        db_session.add(slot)
        await db_session.commit()

        inst1 = InstanciaEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            slot_id=slot.id,
            materia_id=test_materia.id,
            fecha=date(2026, 3, 7),
            hora="18:00",
            titulo="Clase 1 - Semana 1",
        )
        inst2 = InstanciaEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            slot_id=slot.id,
            materia_id=test_materia.id,
            fecha=date(2026, 3, 14),
            hora="18:00",
            titulo="Clase 2 - Semana 2",
        )
        db_session.add_all([inst1, inst2])
        await db_session.commit()

        inst1.estado = EstadoInstancia.REALIZADO.value
        await db_session.commit()
        await db_session.refresh(inst1)
        await db_session.refresh(inst2)

        assert inst1.estado == EstadoInstancia.REALIZADO.value
        assert inst2.estado == EstadoInstancia.PROGRAMADO.value

    @pytest.mark.asyncio
    async def test_instancia_set_cancelado(self, db_session, test_tenant, test_materia):
        instancia = InstanciaEncuentro(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            fecha=date(2026, 4, 1),
            hora="20:00",
            titulo="Clase extra",
            estado=EstadoInstancia.CANCELADO.value,
            meet_url="https://meet.google.com/xyz",
            video_url="https://youtube.com/xyz",
            comentario="Se canceló por feriado",
        )
        db_session.add(instancia)
        await db_session.commit()

        assert instancia.estado == EstadoInstancia.CANCELADO.value
        assert instancia.meet_url == "https://meet.google.com/xyz"
        assert instancia.video_url == "https://youtube.com/xyz"
        assert instancia.comentario == "Se canceló por feriado"


class TestGuardiaModel:

    @pytest.mark.asyncio
    async def test_create_guardia(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        guardia = Guardia(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignacion_id=uuid.uuid4(),
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Viernes",
            horario="16:00–18:00",
        )
        db_session.add(guardia)
        await db_session.commit()

        assert guardia.estado == EstadoGuardia.PENDIENTE.value
        assert guardia.comentarios is None
        assert guardia.dia == "Viernes"

    @pytest.mark.asyncio
    async def test_guardia_estado_enum(self):
        assert EstadoGuardia.PENDIENTE.value == "Pendiente"
        assert EstadoGuardia.REALIZADA.value == "Realizada"
        assert EstadoGuardia.CANCELADA.value == "Cancelada"

    @pytest.mark.asyncio
    async def test_guardia_with_comments(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        guardia = Guardia(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignacion_id=uuid.uuid4(),
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Sábado",
            horario="10:00–12:00",
            estado=EstadoGuardia.REALIZADA.value,
            comentarios="Se cubrió la guardia sin inconvenientes",
        )
        db_session.add(guardia)
        await db_session.commit()

        assert guardia.estado == EstadoGuardia.REALIZADA.value
        assert guardia.comentarios == "Se cubrió la guardia sin inconvenientes"

    @pytest.mark.asyncio
    async def test_guardia_cancelada(self, db_session, test_tenant, test_materia, test_carrera, test_cohorte):
        guardia = Guardia(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignacion_id=uuid.uuid4(),
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            dia="Domingo",
            horario="14:00–16:00",
            estado=EstadoGuardia.CANCELADA.value,
        )
        db_session.add(guardia)
        await db_session.commit()

        assert guardia.estado == EstadoGuardia.CANCELADA.value
