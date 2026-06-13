import pytest
import pytest_asyncio
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.fecha_academica import FechaAcademica, TipoFecha


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


class TestTipoFechaEnum:

    def test_enum_values(self):
        assert TipoFecha.PARCIAL.value == "Parcial"
        assert TipoFecha.TP.value == "TP"
        assert TipoFecha.COLOQUIO.value == "Coloquio"
        assert TipoFecha.RECUPERATORIO.value == "Recuperatorio"


class TestFechaAcademicaModel:

    @pytest.mark.asyncio
    async def test_create_fecha_defaults(self, db_session, test_tenant, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="1er Parcial",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        assert fecha_obj.titulo == "1er Parcial"
        assert fecha_obj.tipo == TipoFecha.PARCIAL.value
        assert fecha_obj.numero == 1
        assert fecha_obj.periodo == "2026"
        assert fecha_obj.fecha == date(2026, 6, 15)
        assert fecha_obj.materia_id == test_materia.id
        assert fecha_obj.cohorte_id == test_cohorte.id

    @pytest.mark.asyncio
    async def test_create_fecha_with_all_tipos(self, db_session, test_tenant, test_materia, test_cohorte):
        for tipo in [TipoFecha.PARCIAL, TipoFecha.TP, TipoFecha.COLOQUIO, TipoFecha.RECUPERATORIO]:
            fecha_obj = FechaAcademica(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                materia_id=test_materia.id,
                cohorte_id=test_cohorte.id,
                tipo=tipo.value,
                numero=1,
                periodo="2026",
                fecha=date(2026, 6, 15),
                titulo=f"Fecha {tipo.value}",
            )
            db_session.add(fecha_obj)
        await db_session.commit()

        query = select(FechaAcademica)
        result = await db_session.execute(query)
        fechas = result.scalars().all()
        assert len(fechas) == 4

    @pytest.mark.asyncio
    async def test_fk_materia(self, db_session, test_tenant, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Test FK",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        fetched = await db_session.get(Materia, test_materia.id)
        assert fetched is not None

    @pytest.mark.asyncio
    async def test_fk_cohorte(self, db_session, test_tenant, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Test FK Cohorte",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        fetched = await db_session.get(Cohorte, test_cohorte.id)
        assert fetched is not None

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session, test_tenant, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="A eliminar",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        from datetime import datetime
        fecha_obj.deleted_at = datetime(2026, 6, 13)
        await db_session.commit()

        query = select(FechaAcademica).where(
            FechaAcademica.id == fecha_obj.id,
            FechaAcademica.deleted_at.is_(None),
        )
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, db_session, test_tenant, test_materia, test_cohorte):
        otro_tenant = Tenant(id=uuid.uuid4(), name="Otro Tenant")
        db_session.add(otro_tenant)
        await db_session.commit()

        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Mi fecha",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        query = select(FechaAcademica).where(
            FechaAcademica.id == fecha_obj.id,
            FechaAcademica.tenant_id == otro_tenant.id,
        )
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is None
