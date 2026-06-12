import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import Usuario
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso, SeveridadAviso
from app.models.carrera import Carrera


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
async def test_user(db_session, test_tenant):
    user = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        _email="user@test.com",
        _dni="12345678",
        _cuil="20-12345678-9",
    )
    db_session.add(user)
    await db_session.commit()
    return user


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


class TestAvisoModel:

    @pytest.mark.asyncio
    async def test_create_aviso_defaults(self, db_session, test_tenant):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Aviso importante",
            cuerpo="Este es un aviso de prueba.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
        )
        db_session.add(aviso)
        await db_session.commit()

        assert aviso.activo is True
        assert aviso.requiere_ack is False
        assert aviso.orden == 0
        assert aviso.severidad == SeveridadAviso.INFO.value

    @pytest.mark.asyncio
    async def test_alcance_enum_values(self):
        assert AlcanceAviso.GLOBAL.value == "Global"
        assert AlcanceAviso.POR_MATERIA.value == "PorMateria"
        assert AlcanceAviso.POR_COHORTE.value == "PorCohorte"
        assert AlcanceAviso.POR_ROL.value == "PorRol"

    @pytest.mark.asyncio
    async def test_severidad_enum_values(self):
        assert SeveridadAviso.INFO.value == "Info"
        assert SeveridadAviso.ADVERTENCIA.value == "Advertencia"
        assert SeveridadAviso.CRITICO.value == "Crítico"

    @pytest.mark.asyncio
    async def test_aviso_with_materia_scope(self, db_session, test_tenant, test_materia):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.POR_MATERIA.value,
            materia_id=test_materia.id,
            titulo="Aviso por materia",
            cuerpo="Solo para esta materia.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
            severidad=SeveridadAviso.ADVERTENCIA.value,
        )
        db_session.add(aviso)
        await db_session.commit()

        assert aviso.alcance == AlcanceAviso.POR_MATERIA.value
        assert aviso.materia_id == test_materia.id
        assert aviso.severidad == SeveridadAviso.ADVERTENCIA.value

    @pytest.mark.asyncio
    async def test_aviso_with_cohorte_scope(self, db_session, test_tenant, test_cohorte):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.POR_COHORTE.value,
            cohorte_id=test_cohorte.id,
            titulo="Aviso por cohorte",
            cuerpo="Solo para esta cohorte.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
        )
        db_session.add(aviso)
        await db_session.commit()

        assert aviso.alcance == AlcanceAviso.POR_COHORTE.value
        assert aviso.cohorte_id == test_cohorte.id

    @pytest.mark.asyncio
    async def test_aviso_with_rol_destino(self, db_session, test_tenant):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.POR_ROL.value,
            rol_destino="PROFESOR",
            titulo="Aviso para profesores",
            cuerpo="Solo para rol profesor.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
            severidad=SeveridadAviso.CRITICO.value,
            orden=5,
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        assert aviso.alcance == AlcanceAviso.POR_ROL.value
        assert aviso.rol_destino == "PROFESOR"
        assert aviso.severidad == SeveridadAviso.CRITICO.value
        assert aviso.orden == 5
        assert aviso.requiere_ack is True

    @pytest.mark.asyncio
    async def test_aviso_ventana_vigencia(self, db_session, test_tenant):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Aviso con vigencia",
            cuerpo="Visible entre inicio y fin.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
        )
        db_session.add(aviso)
        await db_session.commit()

        assert aviso.inicio_en < aviso.fin_en
        assert aviso.inicio_en == datetime(2026, 6, 1)
        assert aviso.fin_en == datetime(2026, 7, 1)


class TestAcknowledgmentAvisoModel:

    @pytest.mark.asyncio
    async def test_create_acknowledgment(self, db_session, test_tenant, test_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Aviso con ack",
            cuerpo="Requiere confirmación.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        ack = AcknowledgmentAviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            aviso_id=aviso.id,
            usuario_id=test_user.id,
            confirmado_at=datetime(2026, 6, 15, 10, 0),
        )
        db_session.add(ack)
        await db_session.commit()

        assert ack.aviso_id == aviso.id
        assert ack.usuario_id == test_user.id
        assert ack.confirmado_at == datetime(2026, 6, 15, 10, 0)

    @pytest.mark.asyncio
    async def test_ack_unique_constraint(self, db_session, test_tenant, test_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Aviso con ack",
            cuerpo="Requiere confirmación.",
            inicio_en=datetime(2026, 6, 1),
            fin_en=datetime(2026, 7, 1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        ack1 = AcknowledgmentAviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            aviso_id=aviso.id,
            usuario_id=test_user.id,
            confirmado_at=datetime(2026, 6, 15, 10, 0),
        )
        db_session.add(ack1)
        await db_session.commit()

        ack2 = AcknowledgmentAviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            aviso_id=aviso.id,
            usuario_id=test_user.id,
            confirmado_at=datetime(2026, 6, 16, 10, 0),
        )
        db_session.add(ack2)

        with pytest.raises(Exception):
            await db_session.commit()
