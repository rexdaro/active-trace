import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.user_role import UserRole
from app.models.rbac import Role
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso, SeveridadAviso
from app.models.audit import AuditLog
from app.services.avisos import AvisoService
from app.schemas.aviso import AvisoCreate, AvisoUpdate

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
async def admin_user(db_session, test_tenant):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=test_tenant.id,
        email="admin@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
        dni="0",
        cuil="0",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def alumno_user(db_session, test_tenant):
    role = Role(name="ALUMNO")
    db_session.add(role)
    await db_session.flush()

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
    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def profesor_role(db_session):
    role = Role(name="PROFESOR")
    db_session.add(role)
    await db_session.commit()
    return role


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


def utc_now():
    return datetime.now(timezone.utc)


class TestCreateAvisoService:

    @pytest.mark.asyncio
    async def test_create_aviso_service(self, db_session, test_tenant, admin_user):
        request = AvisoCreate(
            titulo="Aviso importante",
            cuerpo="Cuerpo del aviso",
            alcance=AlcanceAviso.GLOBAL,
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        result = await AvisoService.create(db_session, request, admin_user)

        assert result.id is not None
        assert result.titulo == "Aviso importante"
        assert result.cuerpo == "Cuerpo del aviso"
        assert result.alcance == AlcanceAviso.GLOBAL.value
        assert result.activo is True
        assert result.tenant_id == test_tenant.id

    @pytest.mark.asyncio
    async def test_create_aviso_audit(self, db_session, test_tenant, admin_user):
        request = AvisoCreate(
            titulo="Aviso con audit",
            cuerpo="Test audit",
            alcance=AlcanceAviso.GLOBAL,
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        await AvisoService.create(db_session, request, admin_user)

        stmt = select(AuditLog).where(AuditLog.action == "AVISO_CREAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        latest = logs[-1]
        assert latest.resource == "avisos"
        assert latest.status == "success"
        assert latest.actor_id == str(admin_user.id)

    @pytest.mark.asyncio
    async def test_create_aviso_por_materia_validates(self, db_session, test_tenant, admin_user, test_materia):
        request = AvisoCreate(
            titulo="Aviso por materia",
            cuerpo="Solo materia",
            alcance=AlcanceAviso.POR_MATERIA,
            materia_id=test_materia.id,
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        result = await AvisoService.create(db_session, request, admin_user)
        assert result.materia_id == test_materia.id

    @pytest.mark.asyncio
    async def test_create_aviso_por_materia_invalid_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        request = AvisoCreate(
            titulo="Aviso materia inválida",
            cuerpo="No existe materia",
            alcance=AlcanceAviso.POR_MATERIA,
            materia_id=uuid.uuid4(),
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        with pytest.raises(HTTPException) as exc:
            await AvisoService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_aviso_por_cohorte_validates(self, db_session, test_tenant, admin_user, test_cohorte):
        request = AvisoCreate(
            titulo="Aviso por cohorte",
            cuerpo="Solo cohorte",
            alcance=AlcanceAviso.POR_COHORTE,
            cohorte_id=test_cohorte.id,
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        result = await AvisoService.create(db_session, request, admin_user)
        assert result.cohorte_id == test_cohorte.id

    @pytest.mark.asyncio
    async def test_create_aviso_por_cohorte_invalid_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        request = AvisoCreate(
            titulo="Aviso cohorte inválida",
            cuerpo="No existe cohorte",
            alcance=AlcanceAviso.POR_COHORTE,
            cohorte_id=uuid.uuid4(),
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        with pytest.raises(HTTPException) as exc:
            await AvisoService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_aviso_por_rol_validates(self, db_session, test_tenant, admin_user, profesor_role):
        request = AvisoCreate(
            titulo="Aviso por rol",
            cuerpo="Solo rol PROFESOR",
            alcance=AlcanceAviso.POR_ROL,
            rol_destino="PROFESOR",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        result = await AvisoService.create(db_session, request, admin_user)
        assert result.rol_destino == "PROFESOR"

    @pytest.mark.asyncio
    async def test_create_aviso_por_rol_invalid(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        request = AvisoCreate(
            titulo="Aviso rol inválido",
            cuerpo="Rol no existe",
            alcance=AlcanceAviso.POR_ROL,
            rol_destino="ROL_INEXISTENTE",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        with pytest.raises(HTTPException) as exc:
            await AvisoService.create(db_session, request, admin_user)
        assert exc.value.status_code == 400


class TestUpdateAvisoService:

    @pytest.mark.asyncio
    async def test_update_aviso_service(self, db_session, test_tenant, admin_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Original",
            cuerpo="Cuerpo original",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        db_session.add(aviso)
        await db_session.commit()

        request = AvisoUpdate(titulo="Modificado", orden=5)
        result = await AvisoService.update(db_session, aviso.id, request, admin_user)

        assert result.titulo == "Modificado"
        assert result.orden == 5
        assert result.cuerpo == "Cuerpo original"

    @pytest.mark.asyncio
    async def test_update_aviso_not_found(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        request = AvisoUpdate(titulo="Nope")
        with pytest.raises(HTTPException) as exc:
            await AvisoService.update(db_session, uuid.uuid4(), request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_aviso_audit(self, db_session, test_tenant, admin_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Original",
            cuerpo="Cuerpo",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        db_session.add(aviso)
        await db_session.commit()

        request = AvisoUpdate(titulo="Modificado")
        await AvisoService.update(db_session, aviso.id, request, admin_user)

        stmt = select(AuditLog).where(AuditLog.action == "AVISO_ACTUALIZAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1


class TestDeleteAvisoService:

    @pytest.mark.asyncio
    async def test_delete_aviso_service(self, db_session, test_tenant, admin_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="A eliminar",
            cuerpo="Será borrado",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        db_session.add(aviso)
        await db_session.commit()

        await AvisoService.delete(db_session, aviso.id, admin_user)

        fetched = await db_session.get(Aviso, aviso.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_aviso_audit(self, db_session, test_tenant, admin_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="A eliminar",
            cuerpo="Audit delete",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        db_session.add(aviso)
        await db_session.commit()

        await AvisoService.delete(db_session, aviso.id, admin_user)

        stmt = select(AuditLog).where(AuditLog.action == "AVISO_ELIMINAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1


class TestGetAvisoService:

    @pytest.mark.asyncio
    async def test_get_aviso(self, db_session, test_tenant, admin_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Visible",
            cuerpo="Solo admin ve",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        db_session.add(aviso)
        await db_session.commit()

        result = await AvisoService.get(db_session, aviso.id, admin_user)
        assert result is not None
        assert result.id == aviso.id

    @pytest.mark.asyncio
    async def test_get_aviso_not_found(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await AvisoService.get(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404


class TestListParaUsuario:

    @pytest.mark.asyncio
    async def test_list_para_usuario_global_visible(self, db_session, test_tenant, alumno_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Aviso global",
            cuerpo="Todos lo ven",
            inicio_en=utc_now() - timedelta(days=1),
            fin_en=utc_now() + timedelta(days=1),
        )
        db_session.add(aviso)
        await db_session.commit()

        results = await AvisoService.list_para_usuario(db_session, alumno_user)
        assert len(results) == 1
        assert results[0].titulo == "Aviso global"
        assert results[0].acknowledged is None

    @pytest.mark.asyncio
    async def test_list_para_usuario_filtra_por_vigencia(self, db_session, test_tenant, alumno_user):
        vencido = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Vencido",
            cuerpo="Ya pasó",
            inicio_en=utc_now() - timedelta(days=10),
            fin_en=utc_now() - timedelta(days=1),
        )
        db_session.add(vencido)
        await db_session.commit()

        results = await AvisoService.list_para_usuario(db_session, alumno_user)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_list_para_usuario_incluye_ack_status(self, db_session, test_tenant, alumno_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Requiere ack",
            cuerpo="Confirmar lectura",
            inicio_en=utc_now() - timedelta(days=1),
            fin_en=utc_now() + timedelta(days=1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        results = await AvisoService.list_para_usuario(db_session, alumno_user)
        assert len(results) == 1
        assert results[0].acknowledged is False

        ack = AcknowledgmentAviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            aviso_id=aviso.id,
            usuario_id=alumno_user.id,
            confirmado_at=utc_now(),
        )
        db_session.add(ack)
        await db_session.commit()

        results2 = await AvisoService.list_para_usuario(db_session, alumno_user)
        assert len(results2) == 1
        assert results2[0].acknowledged is True

    @pytest.mark.asyncio
    async def test_list_para_usuario_filtra_por_rol(self, db_session, test_tenant, alumno_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.POR_ROL.value,
            rol_destino="ALUMNO",
            titulo="Solo alumnos",
            cuerpo="Rol específico",
            inicio_en=utc_now() - timedelta(days=1),
            fin_en=utc_now() + timedelta(days=1),
        )
        db_session.add(aviso)

        aviso_prof = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.POR_ROL.value,
            rol_destino="PROFESOR",
            titulo="Solo profesores",
            cuerpo="No para alumno",
            inicio_en=utc_now() - timedelta(days=1),
            fin_en=utc_now() + timedelta(days=1),
        )
        db_session.add(aviso_prof)
        await db_session.commit()

        results = await AvisoService.list_para_usuario(db_session, alumno_user)
        assert len(results) == 1
        assert results[0].titulo == "Solo alumnos"


class TestConfirmarLectura:

    @pytest.mark.asyncio
    async def test_confirmar_lectura_creates_ack(self, db_session, test_tenant, alumno_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Confirmar",
            cuerpo="Ack this",
            inicio_en=utc_now() - timedelta(days=1),
            fin_en=utc_now() + timedelta(days=1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        ack = await AvisoService.confirmar_lectura(db_session, aviso.id, alumno_user)
        assert ack is not None
        assert ack.aviso_id == aviso.id
        assert ack.usuario_id == alumno_user.id

    @pytest.mark.asyncio
    async def test_confirmar_lectura_idempotent(self, db_session, test_tenant, alumno_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Idempotente",
            cuerpo="Mismo ack",
            inicio_en=utc_now() - timedelta(days=1),
            fin_en=utc_now() + timedelta(days=1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        ack1 = await AvisoService.confirmar_lectura(db_session, aviso.id, alumno_user)
        ack2 = await AvisoService.confirmar_lectura(db_session, aviso.id, alumno_user)
        assert ack1.id == ack2.id

    @pytest.mark.asyncio
    async def test_confirmar_lectura_fuera_vigencia(self, db_session, test_tenant, alumno_user):
        from fastapi import HTTPException
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Vencido",
            cuerpo="Ya expiró",
            inicio_en=utc_now() - timedelta(days=10),
            fin_en=utc_now() - timedelta(days=1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await AvisoService.confirmar_lectura(db_session, aviso.id, alumno_user)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_confirmar_lectura_aviso_not_found(self, db_session, test_tenant, alumno_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await AvisoService.confirmar_lectura(db_session, uuid.uuid4(), alumno_user)
        assert exc.value.status_code == 404


class TestGetMetricas:

    @pytest.mark.asyncio
    async def test_get_metricas_returns_counts(self, db_session, test_tenant, admin_user):
        aviso = Aviso(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            alcance=AlcanceAviso.GLOBAL.value,
            titulo="Metricas",
            cuerpo="Test counts",
            inicio_en=utc_now(),
            fin_en=utc_now() + timedelta(days=30),
        )
        db_session.add(aviso)
        await db_session.commit()

        for _ in range(3):
            u = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"met_{uuid.uuid4()}@t.com", hashed_password="x", dni="0", cuil="0")
            db_session.add(u)
            await db_session.flush()
            ack = AcknowledgmentAviso(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                aviso_id=aviso.id,
                usuario_id=u.id,
                confirmado_at=utc_now(),
            )
            db_session.add(ack)
        await db_session.commit()

        metrics = await AvisoService.get_metricas(db_session, aviso.id, admin_user)
        assert metrics["total_acks"] == 3
        assert metrics["total_views"] == 3

    @pytest.mark.asyncio
    async def test_get_metricas_aviso_not_found(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await AvisoService.get_metricas(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404
