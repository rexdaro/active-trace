import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import Usuario, User
from app.models.rbac import Role
from app.models.asignacion import Asignacion
from app.models.audit import AuditLog
from app.services.equipos import EquiposService
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    ClonarRequest,
    ModificarVigenciaRequest,
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
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_role(db_session):
    role = Role(id=1, name="PROFESOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def mock_user(db_session, test_tenant):
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="coord@test.com",
        hashed_password="hashed_placeholder",
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


def make_asignacion(tenant_id, user_id, role_id, contexto_id, **kw):
    return Asignacion(
        tenant_id=tenant_id,
        user_id=user_id,
        role_id=role_id,
        contexto_id=contexto_id,
        **kw,
    )


# ─── Task 7: mis_equipos ─────────────────────────────────────────────────────

class TestMisEquipos:

    @pytest.mark.asyncio
    async def test_mis_equipos_returns_only_own(self, db_session, mock_user, test_tenant, test_role):
        other_user_id = uuid.uuid4()
        ctx1 = uuid.uuid4()
        ctx2 = uuid.uuid4()

        a_mine = make_asignacion(test_tenant.id, mock_user.id, test_role.id, ctx1,
                                 desde=datetime(2025, 3, 1, tzinfo=timezone.utc))
        a_other = make_asignacion(test_tenant.id, other_user_id, test_role.id, ctx2,
                                  desde=datetime(2025, 3, 1, tzinfo=timezone.utc))
        db_session.add_all([a_mine, a_other])
        await db_session.commit()

        result = await EquiposService.mis_equipos(db_session, mock_user)

        assert len(result) == 1
        assert result[0].user_id == mock_user.id

    @pytest.mark.asyncio
    async def test_mis_equipos_tenant_isolation(self, db_session, mock_user, test_tenant, test_role):
        other_tenant_id = uuid.uuid4()
        a_other = make_asignacion(other_tenant_id, mock_user.id, test_role.id, uuid.uuid4(),
                                  desde=datetime(2025, 3, 1, tzinfo=timezone.utc))
        db_session.add(a_other)
        await db_session.commit()

        result = await EquiposService.mis_equipos(db_session, mock_user)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_mis_equipos_empty(self, db_session, mock_user):
        result = await EquiposService.mis_equipos(db_session, mock_user)
        assert result == []


# ─── Task 8: asignación masiva ──────────────────────────────────────────────

class TestAsignacionMasiva:

    @pytest.mark.asyncio
    async def test_creates_n_asignaciones(self, db_session, mock_user, test_tenant, test_role):
        uid1 = uuid.uuid4()
        uid2 = uuid.uuid4()
        ctx = uuid.uuid4()
        from_date = datetime(2025, 3, 1, tzinfo=timezone.utc)

        request = AsignacionMasivaRequest(asignaciones=[
            {"user_id": uid1, "role_id": test_role.id, "contexto_id": ctx,
             "desde": from_date, "hasta": None},
            {"user_id": uid2, "role_id": test_role.id, "contexto_id": ctx,
             "desde": from_date, "hasta": None},
        ])

        result = await EquiposService.asignar_masiva(db_session, mock_user, request)

        assert result.creadas == 2
        assert len(result.asignaciones) == 2

    @pytest.mark.asyncio
    async def test_creates_with_all_fields(self, db_session, mock_user, test_tenant, test_role):
        ctx = uuid.uuid4()
        from_date = datetime(2025, 3, 1, tzinfo=timezone.utc)
        until_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
        uid = uuid.uuid4()

        request = AsignacionMasivaRequest(asignaciones=[
            {"user_id": uid, "role_id": test_role.id, "contexto_id": ctx,
             "responsable_id": mock_user.id, "desde": from_date, "hasta": until_date},
        ])

        result = await EquiposService.asignar_masiva(db_session, mock_user, request)

        assert result.creadas == 1
        a = result.asignaciones[0]
        assert a.responsable_id == mock_user.id
        assert a.hasta.replace(tzinfo=timezone.utc) == until_date

    @pytest.mark.asyncio
    async def test_audit_logged(self, db_session, mock_user, test_role):
        request = AsignacionMasivaRequest(asignaciones=[
            {"user_id": uuid.uuid4(), "role_id": test_role.id, "contexto_id": uuid.uuid4(),
             "desde": datetime(2025, 3, 1, tzinfo=timezone.utc)},
        ])

        await EquiposService.asignar_masiva(db_session, mock_user, request)

        stmt = select(AuditLog).where(AuditLog.action == "ASIGNACION_MODIFICAR")
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        assert len(logs) == 1
        assert logs[0].filas_afectadas == 1


# ─── Task 9 + 10: clonado ──────────────────────────────────────────────────

class TestClonar:

    @pytest.mark.asyncio
    async def test_clona_solo_activas(self, db_session, mock_user, test_tenant, test_role):
        now = datetime.now(timezone.utc)
        origen = uuid.uuid4()
        destino = uuid.uuid4()
        nuevo_desde = datetime(2026, 3, 1, tzinfo=timezone.utc)
        nuevo_hasta = datetime(2026, 12, 31, tzinfo=timezone.utc)

        activa_sin_hasta = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, origen,
            desde=now - timedelta(days=30),
        )
        activa_con_hasta = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, origen,
            desde=now - timedelta(days=30), hasta=now + timedelta(days=30),
        )
        vencida = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, origen,
            desde=now - timedelta(days=60), hasta=now - timedelta(days=1),
        )
        db_session.add_all([activa_sin_hasta, activa_con_hasta, vencida])
        await db_session.commit()

        request = ClonarRequest(
            origen_contexto_id=origen,
            destino_contexto_id=destino,
            nuevo_desde=nuevo_desde,
            nuevo_hasta=nuevo_hasta,
        )

        result = await EquiposService.clonar(db_session, mock_user, request)

        assert result.clonadas == 2
        assert len(result.asignaciones) == 2
        for a in result.asignaciones:
            assert a.contexto_id == destino
            assert a.desde.replace(tzinfo=timezone.utc) == nuevo_desde
            assert a.hasta.replace(tzinfo=timezone.utc) == nuevo_hasta

    @pytest.mark.asyncio
    async def test_clonar_sin_activas(self, db_session, mock_user, test_tenant, test_role):
        now = datetime.now(timezone.utc)
        origen = uuid.uuid4()
        destino = uuid.uuid4()

        vencida = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, origen,
            desde=now - timedelta(days=60), hasta=now - timedelta(days=1),
        )
        db_session.add(vencida)
        await db_session.commit()

        request = ClonarRequest(
            origen_contexto_id=origen,
            destino_contexto_id=destino,
            nuevo_desde=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )

        result = await EquiposService.clonar(db_session, mock_user, request)

        assert result.clonadas == 0
        assert result.asignaciones == []

    @pytest.mark.asyncio
    async def test_clonar_audit_logged(self, db_session, mock_user, test_tenant, test_role):
        now = datetime.now(timezone.utc)
        origen = uuid.uuid4()
        destino = uuid.uuid4()

        activa = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, origen,
            desde=now - timedelta(days=30),
        )
        db_session.add(activa)
        await db_session.commit()

        request = ClonarRequest(
            origen_contexto_id=origen,
            destino_contexto_id=destino,
            nuevo_desde=now,
        )
        await EquiposService.clonar(db_session, mock_user, request)

        stmt = select(AuditLog).where(AuditLog.action == "ASIGNACION_MODIFICAR")
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        assert len(logs) == 1


# ─── Task 11: modificación de vigencia ──────────────────────────────────────

class TestModificarVigencia:

    @pytest.mark.asyncio
    async def test_modifica_solo_contexto_correcto(self, db_session, mock_user, test_tenant, test_role):
        ctx_a = uuid.uuid4()
        ctx_b = uuid.uuid4()
        original_desde = datetime(2025, 1, 1, tzinfo=timezone.utc)
        new_desde = datetime(2026, 3, 1, tzinfo=timezone.utc)
        new_hasta = datetime(2026, 12, 31, tzinfo=timezone.utc)

        for _ in range(3):
            a = make_asignacion(
                test_tenant.id, mock_user.id, test_role.id, ctx_a,
                desde=original_desde,
            )
            db_session.add(a)

        a_otro = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, ctx_b,
            desde=original_desde,
        )
        db_session.add(a_otro)
        await db_session.commit()

        request = ModificarVigenciaRequest(
            contexto_id=ctx_a,
            nuevo_desde=new_desde,
            nuevo_hasta=new_hasta,
        )
        result = await EquiposService.modificar_vigencia(db_session, mock_user, request)

        assert result.modificadas == 3

    @pytest.mark.asyncio
    async def test_no_modifica_otro_contexto(self, db_session, mock_user, test_tenant, test_role):
        ctx_a = uuid.uuid4()
        ctx_b = uuid.uuid4()
        original_desde = datetime(2025, 1, 1, tzinfo=timezone.utc)

        a_a = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, ctx_a,
            desde=original_desde,
        )
        a_b = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, ctx_b,
            desde=original_desde,
        )
        db_session.add_all([a_a, a_b])
        await db_session.commit()

        request = ModificarVigenciaRequest(
            contexto_id=ctx_a,
            nuevo_desde=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        await EquiposService.modificar_vigencia(db_session, mock_user, request)

        stmt = select(Asignacion).where(Asignacion.contexto_id == ctx_b)
        result = await db_session.execute(stmt)
        b_asigs = result.scalars().all()
        assert b_asigs[0].desde == original_desde


# ─── Task 12: export CSV ──────────────────────────────────────────────────

class TestExportar:

    @pytest.mark.asyncio
    async def test_export_tiene_bom_y_headers(self, db_session, mock_user, test_tenant, test_role):
        ctx = uuid.uuid4()
        a = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, ctx,
            desde=datetime(2025, 3, 1, tzinfo=timezone.utc),
        )
        db_session.add(a)
        await db_session.commit()

        csv_content = await EquiposService.exportar(db_session, mock_user, ctx)

        assert csv_content.startswith("\ufeff")
        lines = csv_content.splitlines()
        assert len(lines) >= 2
        header = lines[0]
        assert "user_id" in header
        assert "email" in header
        assert "dni" in header
        assert "rol" in header
        assert "estado_vigencia" in header

    @pytest.mark.asyncio
    async def test_export_contiene_datos(self, db_session, mock_user, test_tenant, test_role):
        ctx = uuid.uuid4()
        a = make_asignacion(
            test_tenant.id, mock_user.id, test_role.id, ctx,
            desde=datetime(2020, 1, 1, tzinfo=timezone.utc),
            hasta=datetime(2099, 12, 31, tzinfo=timezone.utc),
        )
        db_session.add(a)
        await db_session.commit()

        csv_content = await EquiposService.exportar(db_session, mock_user, ctx)
        lines = csv_content.splitlines()
        assert len(lines) == 2
        assert "vigente" in lines[1]

    @pytest.mark.asyncio
    async def test_export_csv_header_format(self, db_session, mock_user, test_tenant, test_role):
        ctx = uuid.uuid4()
        csv_content = await EquiposService.exportar(db_session, mock_user, ctx)
        header = csv_content.lstrip("\ufeff").splitlines()[0]
        assert header == "user_id,email,dni,nombre,rol,contexto_id,responsable_id,desde,hasta,estado_vigencia"


# ─── Task 14: tenant isolation ──────────────────────────────────────────────

class TestTenantIsolation:

    @pytest.mark.asyncio
    async def test_tenant_no_ve_otros_datos(self, db_session, test_role):
        tenant_a_id = uuid.uuid4()
        tenant_b_id = uuid.uuid4()

        user_a = User(id=uuid.uuid4(), tenant_id=tenant_a_id, email="a@test.com",
                       hashed_password="ph", is_2fa_enabled=False)
        user_b = User(id=uuid.uuid4(), tenant_id=tenant_b_id, email="b@test.com",
                       hashed_password="ph", is_2fa_enabled=False)
        db_session.add_all([user_a, user_b])

        ctx = uuid.uuid4()
        a_a = make_asignacion(tenant_a_id, user_a.id, test_role.id, ctx,
                              desde=datetime(2025, 3, 1, tzinfo=timezone.utc))
        a_b = make_asignacion(tenant_b_id, user_b.id, test_role.id, ctx,
                              desde=datetime(2025, 3, 1, tzinfo=timezone.utc))
        db_session.add_all([a_a, a_b])
        await db_session.commit()

        result_a = await EquiposService.mis_equipos(db_session, user_a)

        assert len(result_a) == 1
        assert result_a[0].tenant_id == tenant_a_id
