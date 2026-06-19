import pytest
import pytest_asyncio
import uuid
import os
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import Usuario
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.asignacion import Asignacion
from app.models.salario import SalarioBase, SalarioPlus
from app.models.liquidacion import Liquidacion, Factura, EstadoLiquidacion, EstadoFactura
from app.repositories.salarios import SalarioBaseRepository, SalarioPlusRepository
from app.repositories.liquidaciones import LiquidacionRepository, FacturaRepository
from app.services.liquidaciones import LiquidacionService, FacturaService
from app.schemas.factura import FacturaCreate

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
async def test_usuario(db_session, test_tenant):
    usuario = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="docente@test.com",
        hashed_password="x",
        _dni="12345678",
        _cuil="20123456789",
    )
    db_session.add(usuario)
    await db_session.commit()
    return usuario


@pytest_asyncio.fixture
async def test_carrera(db_session, test_tenant):
    carrera = Carrera(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Test", code="TST")
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
async def admin_user(db_session, test_tenant):
    user = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="admin@test.com",
        hashed_password="x",
        _dni="99999999",
        _cuil="20999999999",
    )
    db_session.add(user)
    await db_session.commit()
    return user


class TestSalarioBase:

    async def test_create_salario_base(self, db_session, test_tenant):
        repo = SalarioBaseRepository(db_session)
        obj = await repo.create(
            {"rol": "PROFESOR", "monto": Decimal("50000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await db_session.commit()
        assert obj.id is not None
        assert obj.rol == "PROFESOR"
        assert obj.monto == Decimal("50000")
        assert obj.desde == date(2026, 1, 1)
        assert obj.hasta is None

    async def test_get_salario_base(self, db_session, test_tenant):
        repo = SalarioBaseRepository(db_session)
        obj = await repo.create(
            {"rol": "TUTOR", "monto": Decimal("30000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await db_session.commit()
        fetched = await repo.get(obj.id, test_tenant.id)
        assert fetched is not None
        assert fetched.rol == "TUTOR"

    async def test_get_not_found_other_tenant(self, db_session, test_tenant):
        repo = SalarioBaseRepository(db_session)
        obj = await repo.create(
            {"rol": "PROFESOR", "monto": Decimal("50000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await db_session.commit()
        other_tenant_id = uuid.uuid4()
        fetched = await repo.get(obj.id, other_tenant_id)
        assert fetched is None

    async def test_update_salario_base(self, db_session, test_tenant):
        repo = SalarioBaseRepository(db_session)
        obj = await repo.create(
            {"rol": "PROFESOR", "monto": Decimal("50000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await db_session.commit()
        await repo.update(obj, {"monto": Decimal("55000")})
        await db_session.commit()
        assert obj.monto == Decimal("55000")

    async def test_list_salarios_base(self, db_session, test_tenant):
        repo = SalarioBaseRepository(db_session)
        await repo.create({"rol": "PROFESOR", "monto": Decimal("50000"), "desde": date(2026, 1, 1)}, test_tenant.id)
        await repo.create({"rol": "TUTOR", "monto": Decimal("30000"), "desde": date(2026, 1, 1)}, test_tenant.id)
        await db_session.commit()
        items = await repo.list(test_tenant.id)
        assert len(items) == 2

    async def test_vigente_por_rol(self, db_session, test_tenant):
        repo = SalarioBaseRepository(db_session)
        await repo.create(
            {"rol": "PROFESOR", "monto": Decimal("40000"), "desde": date(2025, 1, 1), "hasta": date(2025, 12, 31)},
            test_tenant.id,
        )
        await repo.create(
            {"rol": "PROFESOR", "monto": Decimal("50000"), "desde": date(2026, 1, 1), "hasta": None},
            test_tenant.id,
        )
        await db_session.commit()

        vigente = await repo.get_vigente(test_tenant.id, "PROFESOR", date(2026, 6, 1))
        assert vigente is not None
        assert vigente.monto == Decimal("50000")

        vigente_2025 = await repo.get_vigente(test_tenant.id, "PROFESOR", date(2025, 6, 1))
        assert vigente_2025 is not None
        assert vigente_2025.monto == Decimal("40000")


class TestSalarioPlus:

    async def test_create_salario_plus(self, db_session, test_tenant):
        repo = SalarioPlusRepository(db_session)
        obj = await repo.create(
            {
                "grupo": "GrupoA",
                "rol": "PROFESOR",
                "descripcion": "Plus por antiguedad",
                "monto": Decimal("5000"),
                "desde": date(2026, 1, 1),
            },
            test_tenant.id,
        )
        await db_session.commit()
        assert obj.id is not None
        assert obj.monto == Decimal("5000")

    async def test_list_salarios_plus(self, db_session, test_tenant):
        repo = SalarioPlusRepository(db_session)
        await repo.create(
            {"grupo": "GrupoA", "rol": "PROFESOR", "descripcion": "Plus1", "monto": Decimal("5000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await repo.create(
            {"grupo": "GrupoB", "rol": "TUTOR", "descripcion": "Plus2", "monto": Decimal("3000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await db_session.commit()
        items = await repo.list(test_tenant.id)
        assert len(items) == 2

    async def test_update_salario_plus(self, db_session, test_tenant):
        repo = SalarioPlusRepository(db_session)
        obj = await repo.create(
            {"grupo": "GrupoA", "rol": "PROFESOR", "descripcion": "Plus", "monto": Decimal("5000"), "desde": date(2026, 1, 1)},
            test_tenant.id,
        )
        await db_session.commit()
        await repo.update(obj, {"monto": Decimal("6000")})
        await db_session.commit()
        assert obj.monto == Decimal("6000")


class TestLiquidacion:

    async def test_create_liquidacion(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        liq = await repo.create(
            {
                "cohorte_id": test_cohorte.id,
                "periodo": "2026-06",
                "usuario_id": test_usuario.id,
                "rol": "PROFESOR",
                "monto_base": Decimal("50000"),
                "monto_plus": Decimal("5000"),
                "total": Decimal("55000"),
                "es_nexo": False,
            },
            test_tenant.id,
        )
        await db_session.commit()
        assert liq.id is not None
        assert liq.total == Decimal("55000")
        assert liq.estado == EstadoLiquidacion.ABIERTA.value

    async def test_liquidacion_default_abierta(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        liq = await repo.create(
            {
                "cohorte_id": test_cohorte.id,
                "periodo": "2026-06",
                "usuario_id": test_usuario.id,
                "rol": "TUTOR",
                "monto_base": Decimal("30000"),
                "monto_plus": Decimal("0"),
                "total": Decimal("30000"),
            },
            test_tenant.id,
        )
        await db_session.commit()
        assert liq.estado == "Abierta"

    async def test_cerrar_liquidacion(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        liq = await repo.create(
            {
                "cohorte_id": test_cohorte.id,
                "periodo": "2026-06",
                "usuario_id": test_usuario.id,
                "rol": "PROFESOR",
                "monto_base": Decimal("50000"),
                "monto_plus": Decimal("0"),
                "total": Decimal("50000"),
            },
            test_tenant.id,
        )
        await db_session.commit()

        cerrada = await LiquidacionService.cerrar(
            db_session, liq.id, test_tenant.id, str(uuid.uuid4())
        )
        assert cerrada.estado == EstadoLiquidacion.CERRADA.value

    async def test_cerrar_ya_cerrada_rechaza(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        liq = await repo.create(
            {
                "cohorte_id": test_cohorte.id,
                "periodo": "2026-06",
                "usuario_id": test_usuario.id,
                "rol": "PROFESOR",
                "monto_base": Decimal("50000"),
                "monto_plus": Decimal("0"),
                "total": Decimal("50000"),
            },
            test_tenant.id,
        )
        await db_session.commit()

        await LiquidacionService.cerrar(db_session, liq.id, test_tenant.id, str(uuid.uuid4()))
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await LiquidacionService.cerrar(db_session, liq.id, test_tenant.id, str(uuid.uuid4()))
        assert exc.value.status_code == 400

    async def test_list_liquidaciones_by_periodo(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        for p in ["2026-05", "2026-06"]:
            await repo.create(
                {"cohorte_id": test_cohorte.id, "periodo": p, "usuario_id": test_usuario.id,
                 "rol": "PROFESOR", "monto_base": Decimal("50000"), "monto_plus": Decimal("0"),
                 "total": Decimal("50000")},
                test_tenant.id,
            )
        await db_session.commit()

        items = await repo.list(test_tenant.id, periodo="2026-06")
        assert len(items) == 1
        assert items[0].periodo == "2026-06"

    async def test_excluido_por_factura_default(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        liq = await repo.create(
            {
                "cohorte_id": test_cohorte.id,
                "periodo": "2026-06",
                "usuario_id": test_usuario.id,
                "rol": "NEXO",
                "monto_base": Decimal("20000"),
                "monto_plus": Decimal("0"),
                "total": Decimal("20000"),
                "es_nexo": True,
            },
            test_tenant.id,
        )
        await db_session.commit()
        assert liq.excluido_por_factura is False

    async def test_liquidacion_tenant_isolation(self, db_session, test_tenant, test_cohorte, test_usuario):
        repo = LiquidacionRepository(db_session)
        liq = await repo.create(
            {
                "cohorte_id": test_cohorte.id,
                "periodo": "2026-06",
                "usuario_id": test_usuario.id,
                "rol": "PROFESOR",
                "monto_base": Decimal("50000"),
                "monto_plus": Decimal("0"),
                "total": Decimal("50000"),
            },
            test_tenant.id,
        )
        await db_session.commit()

        other_tenant_id = uuid.uuid4()
        fetched = await repo.get(liq.id, other_tenant_id)
        assert fetched is None


class TestFactura:

    async def test_create_factura(self, db_session, test_tenant, test_usuario):
        repo = FacturaRepository(db_session)
        factura = await repo.create(
            {
                "usuario_id": test_usuario.id,
                "periodo": "2026-06",
                "detalle": "Honorarios junio 2026",
            },
            test_tenant.id,
        )
        await db_session.commit()
        assert factura.id is not None
        assert factura.estado == EstadoFactura.PENDIENTE.value

    async def test_factura_default_pendiente(self, db_session, test_tenant, test_usuario):
        repo = FacturaRepository(db_session)
        factura = await repo.create(
            {"usuario_id": test_usuario.id, "periodo": "2026-06", "detalle": "Test"},
            test_tenant.id,
        )
        await db_session.commit()
        assert factura.estado == "Pendiente"

    async def test_abonar_factura(self, db_session, test_tenant, test_usuario):
        repo = FacturaRepository(db_session)
        factura = await repo.create(
            {"usuario_id": test_usuario.id, "periodo": "2026-06", "detalle": "Test"},
            test_tenant.id,
        )
        await db_session.commit()

        abonada = await FacturaService.abonar(
            db_session, factura.id, test_tenant.id, str(uuid.uuid4())
        )
        assert abonada.estado == EstadoFactura.ABONADA.value
        assert abonada.abonada_at is not None

    async def test_abonar_ya_abonada_rechaza(self, db_session, test_tenant, test_usuario):
        repo = FacturaRepository(db_session)
        factura = await repo.create(
            {"usuario_id": test_usuario.id, "periodo": "2026-06", "detalle": "Test"},
            test_tenant.id,
        )
        await db_session.commit()

        await FacturaService.abonar(db_session, factura.id, test_tenant.id, str(uuid.uuid4()))
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await FacturaService.abonar(db_session, factura.id, test_tenant.id, str(uuid.uuid4()))
        assert exc.value.status_code == 400

    async def test_factura_tenant_isolation(self, db_session, test_tenant, test_usuario):
        repo = FacturaRepository(db_session)
        factura = await repo.create(
            {"usuario_id": test_usuario.id, "periodo": "2026-06", "detalle": "Test"},
            test_tenant.id,
        )
        await db_session.commit()

        other_tenant_id = uuid.uuid4()
        fetched = await repo.get(factura.id, other_tenant_id)
        assert fetched is None

    async def test_list_facturas(self, db_session, test_tenant, test_usuario):
        repo = FacturaRepository(db_session)
        await repo.create(
            {"usuario_id": test_usuario.id, "periodo": "2026-06", "detalle": "Factura 1"},
            test_tenant.id,
        )
        await repo.create(
            {"usuario_id": test_usuario.id, "periodo": "2026-07", "detalle": "Factura 2"},
            test_tenant.id,
        )
        await db_session.commit()

        items = await repo.list(test_tenant.id)
        assert len(items) == 2

        items_jun = await repo.list(test_tenant.id, periodo="2026-06")
        assert len(items_jun) == 1
