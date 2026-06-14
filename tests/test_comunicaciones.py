import pytest
import pytest_asyncio
import uuid
import os
import time
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.padron import VersionPadron, EntradaPadron
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.models.audit import AuditLog
from app.repositories.comunicaciones import ComunicacionesRepository
from app.services.comunicaciones import ComunicacionesService
from app.schemas.comunicacion import PreviewRequest, ConfirmRequest

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
async def test_tenant_with_approval(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Approval Tenant", requiere_aprobacion=True)
    db_session.add(tenant)
    await db_session.commit()
    return tenant


@pytest_asyncio.fixture
async def mock_user(db_session, test_tenant):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=test_tenant.id,
        email="teacher@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    usuario = Usuario(
        id=uid,
        tenant_id=test_tenant.id,
        email="teacher@test.com",
        dni="0",
        cuil="0",
    )
    db_session.add_all([user, usuario])
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def mock_user_approval(db_session, test_tenant_with_approval):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=test_tenant_with_approval.id,
        email="teacher@approval.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    usuario = Usuario(
        id=uid,
        tenant_id=test_tenant_with_approval.id,
        email="teacher@approval.com",
        dni="0",
        cuil="0",
    )
    db_session.add_all([user, usuario])
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_materia(db_session, test_tenant):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="MAT101", is_active=True)
    db_session.add(materia)
    await db_session.commit()
    return materia


@pytest_asyncio.fixture
async def test_materia_approval(db_session, test_tenant_with_approval):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant_with_approval.id, name="Física", code="FIS101", is_active=True)
    db_session.add(materia)
    await db_session.commit()
    return materia


@pytest_asyncio.fixture
async def test_carrera(db_session, test_tenant):
    carrera = Carrera(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Ingeniería", code="ING", is_active=True)
    db_session.add(carrera)
    await db_session.commit()
    return carrera


@pytest_asyncio.fixture
async def test_cohorte(db_session, test_tenant, test_carrera):
    cohorte = Cohorte(id=uuid.uuid4(), tenant_id=test_tenant.id, name="2025", carrera_id=test_carrera.id, is_active=True)
    db_session.add(cohorte)
    await db_session.commit()
    return cohorte


@pytest_asyncio.fixture
async def test_carrera_approval(db_session, test_tenant_with_approval):
    carrera = Carrera(id=uuid.uuid4(), tenant_id=test_tenant_with_approval.id, name="Medicina", code="MED", is_active=True)
    db_session.add(carrera)
    await db_session.commit()
    return carrera


@pytest_asyncio.fixture
async def test_cohorte_approval(db_session, test_tenant_with_approval, test_carrera_approval):
    cohorte = Cohorte(id=uuid.uuid4(), tenant_id=test_tenant_with_approval.id, name="2025", carrera_id=test_carrera_approval.id, is_active=True)
    db_session.add(cohorte)
    await db_session.commit()
    return cohorte


@pytest_asyncio.fixture
async def test_entrada_padron(db_session, test_tenant, test_materia, mock_user, test_cohorte):
    version = VersionPadron(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        materia_id=test_materia.id,
        cohorte_id=test_cohorte.id,
        archivo_nombre="padron.csv",
        archivo_hash="abc123",
        origen="Archivo",
        cargado_por=mock_user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.commit()

    entrada = EntradaPadron(
        id=uuid.uuid4(),
        version_id=version.id,
        tenant_id=test_tenant.id,
        usuario_id=None,
        nombre="Juan",
        apellidos="Pérez",
        email="juan@test.com",
        comision="A",
        regional="CABA",
    )
    db_session.add(entrada)
    await db_session.commit()
    return entrada


@pytest_asyncio.fixture
async def test_entrada_padron2(db_session, test_tenant, test_materia, mock_user, test_cohorte):
    version = VersionPadron(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        materia_id=test_materia.id,
        cohorte_id=test_cohorte.id,
        archivo_nombre="padron.csv",
        archivo_hash="abc456",
        origen="Archivo",
        cargado_por=mock_user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.commit()

    entrada = EntradaPadron(
        id=uuid.uuid4(),
        version_id=version.id,
        tenant_id=test_tenant.id,
        usuario_id=None,
        nombre="María",
        apellidos="García",
        email="maria@test.com",
        comision="B",
        regional="CABA",
    )
    db_session.add(entrada)
    await db_session.commit()
    return entrada


@pytest_asyncio.fixture
async def test_entrada_padron_approval(db_session, test_tenant_with_approval, test_materia_approval, mock_user_approval, test_cohorte_approval):
    version = VersionPadron(
        id=uuid.uuid4(),
        tenant_id=test_tenant_with_approval.id,
        materia_id=test_materia_approval.id,
        cohorte_id=test_cohorte_approval.id,
        archivo_nombre="padron.csv",
        archivo_hash="abc789",
        origen="Archivo",
        cargado_por=mock_user_approval.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.commit()

    entrada = EntradaPadron(
        id=uuid.uuid4(),
        version_id=version.id,
        tenant_id=test_tenant_with_approval.id,
        usuario_id=None,
        nombre="Carlos",
        apellidos="López",
        email="carlos@test.com",
        comision="C",
        regional="Córdoba",
    )
    db_session.add(entrada)
    await db_session.commit()
    return entrada


# ═══════════════════════════════════════════════════════════════════════════════
# Task 14: State Machine Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRepoStateMachine:

    @pytest.mark.asyncio
    async def test_pendiente_to_enviando(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.PENDIENTE.value,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.transition_state(c.id, ComunicacionEstado.PENDIENTE.value, ComunicacionEstado.ENVIANDO.value, test_tenant.id)
        assert result is not None
        assert result.estado == ComunicacionEstado.ENVIANDO.value

    @pytest.mark.asyncio
    async def test_pendiente_to_cancelado(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.PENDIENTE.value,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.transition_state(c.id, ComunicacionEstado.PENDIENTE.value, ComunicacionEstado.CANCELADO.value, test_tenant.id)
        assert result is not None
        assert result.estado == ComunicacionEstado.CANCELADO.value

    @pytest.mark.asyncio
    async def test_pendiente_enviando_enviado_full_path(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.PENDIENTE.value,
        )
        db_session.add(c)
        await db_session.commit()

        r1 = await repo.transition_state(c.id, ComunicacionEstado.PENDIENTE.value, ComunicacionEstado.ENVIANDO.value, test_tenant.id)
        assert r1 is not None
        assert r1.estado == ComunicacionEstado.ENVIANDO.value

        r2 = await repo.transition_state(c.id, ComunicacionEstado.ENVIANDO.value, ComunicacionEstado.ENVIADO.value, test_tenant.id)
        assert r2 is not None
        assert r2.estado == ComunicacionEstado.ENVIADO.value

    @pytest.mark.asyncio
    async def test_pendiente_enviando_error_full_path(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.PENDIENTE.value,
        )
        db_session.add(c)
        await db_session.commit()

        r1 = await repo.transition_state(c.id, ComunicacionEstado.PENDIENTE.value, ComunicacionEstado.ENVIANDO.value, test_tenant.id)
        assert r1 is not None
        assert r1.estado == ComunicacionEstado.ENVIANDO.value

        r2 = await repo.transition_state(c.id, ComunicacionEstado.ENVIANDO.value, ComunicacionEstado.ERROR.value, test_tenant.id)
        assert r2 is not None
        assert r2.estado == ComunicacionEstado.ERROR.value

    @pytest.mark.asyncio
    async def test_enviando_to_cancelado_invalid(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.ENVIANDO.value,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.transition_state(c.id, ComunicacionEstado.ENVIANDO.value, ComunicacionEstado.CANCELADO.value, test_tenant.id)
        assert result is not None
        assert result.estado == ComunicacionEstado.CANCELADO.value

    @pytest.mark.asyncio
    async def test_enviado_to_enviando_is_atomic(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.ENVIADO.value,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.transition_state(c.id, ComunicacionEstado.ENVIADO.value, ComunicacionEstado.ENVIANDO.value, test_tenant.id)
        assert result is not None
        assert result.estado == ComunicacionEstado.ENVIANDO.value

    @pytest.mark.asyncio
    async def test_transition_state_wrong_state_returns_none(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.PENDIENTE.value,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.transition_state(c.id, ComunicacionEstado.ENVIANDO.value, ComunicacionEstado.CANCELADO.value, test_tenant.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_wrong_tenant_returns_none(self, db_session, test_tenant, mock_user, test_materia):
        repo = ComunicacionesRepository(db_session)
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.PENDIENTE.value,
        )
        db_session.add(c)
        await db_session.commit()

        otro_tenant = uuid.uuid4()
        result = await repo.transition_state(c.id, ComunicacionEstado.PENDIENTE.value, ComunicacionEstado.ENVIANDO.value, otro_tenant)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# Task 15: Preview Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPreview:

    @pytest.mark.asyncio
    async def test_preview_valid_ids_returns_rendered_items(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        request = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Hola {{nombre}}",
            cuerpo="Bienvenido {{nombre}} {{apellidos}} a {{materia}}",
            materia_id=test_materia.id,
        )
        response = await ComunicacionesService.preview(db_session, request, mock_user)

        assert response.preview_token is not None
        assert len(response.items) == 1
        assert response.total == 1
        assert response.items[0].nombre == "Juan"
        assert response.items[0].asunto_renderizado == "Hola Juan"
        assert response.items[0].cuerpo_renderizado == "Bienvenido Juan Pérez a Matemática"

    @pytest.mark.asyncio
    async def test_preview_multiple_destinatarios(
        self, db_session, test_tenant, test_materia, test_entrada_padron, test_entrada_padron2, mock_user
    ):
        request = PreviewRequest(
            destinatarios=[test_entrada_padron.id, test_entrada_padron2.id],
            asunto="Clase {{materia}}",
            cuerpo="Hola {{nombre}}",
            materia_id=test_materia.id,
        )
        response = await ComunicacionesService.preview(db_session, request, mock_user)

        assert response.total == 2
        nombres = {i.nombre for i in response.items}
        assert nombres == {"Juan", "María"}

    @pytest.mark.asyncio
    async def test_preview_missing_variable_raises_error(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        request = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Hola {{nombre}}",
            cuerpo="Variable {{inexistente}} no definida",
            materia_id=test_materia.id,
        )
        from jinja2 import UndefinedError
        with pytest.raises(UndefinedError):
            await ComunicacionesService.preview(db_session, request, mock_user)

    @pytest.mark.asyncio
    async def test_preview_con_materia_en_template(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        request = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="[{{materia}}] Aviso importante",
            cuerpo="Estimado {{nombre}}, le informamos sobre {{materia}}.",
            materia_id=test_materia.id,
        )
        response = await ComunicacionesService.preview(db_session, request, mock_user)

        assert "[Matemática] Aviso importante" == response.items[0].asunto_renderizado
        assert "Matemática" in response.items[0].cuerpo_renderizado

    @pytest.mark.asyncio
    async def test_preview_unknown_id_reported_in_errores(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        fake_id = uuid.uuid4()
        request = PreviewRequest(
            destinatarios=[test_entrada_padron.id, fake_id],
            asunto="Hola {{nombre}}",
            cuerpo="Test",
            materia_id=test_materia.id,
        )
        response = await ComunicacionesService.preview(db_session, request, mock_user)
        assert len(response.errores) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Task 15-16: Confirm Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfirm:

    @pytest.mark.asyncio
    async def test_confirm_creates_records_with_same_lote(
        self, db_session, test_tenant, test_materia, test_entrada_padron, test_entrada_padron2, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id, test_entrada_padron2.id],
            asunto="Clase {{materia}}",
            cuerpo="Hola {{nombre}}",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        token = preview_resp.preview_token

        confirm_req = ConfirmRequest(preview_token=token)
        confirm_resp = await ComunicacionesService.confirm(db_session, confirm_req, mock_user)

        assert confirm_resp.cantidad == 2
        assert confirm_resp.lote_id is not None

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant.id)
        assert len(comunicaciones) == 2
        for c in comunicaciones:
            assert c.lote_id == confirm_resp.lote_id

    @pytest.mark.asyncio
    async def test_confirm_sin_aprobacion(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        assert confirm_resp.requiere_aprobacion is False

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant.id)
        assert len(comunicaciones) == 1
        assert comunicaciones[0].estado == ComunicacionEstado.PENDIENTE.value
        assert comunicaciones[0].lote_aprobado is False

    @pytest.mark.asyncio
    async def test_confirm_con_aprobacion(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        assert confirm_resp.requiere_aprobacion is True

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant_with_approval.id)
        assert len(comunicaciones) == 1
        assert comunicaciones[0].estado == ComunicacionEstado.PENDIENTE.value
        assert comunicaciones[0].lote_aprobado is False

    @pytest.mark.asyncio
    async def test_confirm_audit_log_creado(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        stmt = select(AuditLog).where(AuditLog.action == "COMUNICACION_ENVIAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) == 1
        assert logs[0].status == "success"
        assert logs[0].filas_afectadas == 1

    @pytest.mark.asyncio
    async def test_confirm_invalid_token_400(
        self, db_session, mock_user
    ):
        with pytest.raises(Exception) as exc:
            await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token="invalid-token"), mock_user)
        assert exc.type.__name__ == "HTTPException"

    @pytest.mark.asyncio
    async def test_confirm_expired_token_400(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)

        token = preview_resp.preview_token
        ComunicacionesService._preview_store[token]["timestamp"] = 0

        with pytest.raises(Exception) as exc:
            await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=token), mock_user)
        assert exc.type.__name__ == "HTTPException"


# ═══════════════════════════════════════════════════════════════════════════════
# Task 17: Approval Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestApproval:

    @pytest.mark.asyncio
    async def test_approve_lote_transitions_all(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        result = await ComunicacionesService.aprobar_lote(db_session, confirm_resp.lote_id, mock_user_approval)
        assert result.transicionados == 1
        assert result.lote_id == confirm_resp.lote_id

    @pytest.mark.asyncio
    async def test_approve_lote_sets_enviando_and_lote_aprobado(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        await ComunicacionesService.aprobar_lote(db_session, confirm_resp.lote_id, mock_user_approval)

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant_with_approval.id)
        assert len(comunicaciones) == 1
        assert comunicaciones[0].estado == ComunicacionEstado.ENVIANDO.value
        assert comunicaciones[0].lote_aprobado is True

    @pytest.mark.asyncio
    async def test_approve_single_only_that_message(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        entrada2 = EntradaPadron(
            id=uuid.uuid4(),
            version_id=test_entrada_padron_approval.version_id,
            tenant_id=test_tenant_with_approval.id,
            nombre="Ana",
            apellidos="Martínez",
            email="ana@test.com",
        )
        db_session.add(entrada2)
        await db_session.commit()

        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id, entrada2.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant_with_approval.id)

        target_id = comunicaciones[0].id
        result = await ComunicacionesService.aprobar_individual(db_session, target_id, mock_user_approval)
        assert result.estado == ComunicacionEstado.ENVIANDO.value

        updated = await repo.get_by_lote(confirm_resp.lote_id, test_tenant_with_approval.id)
        otros = [c for c in updated if c.id != target_id]
        assert len(otros) == 1
        assert otros[0].estado == ComunicacionEstado.PENDIENTE.value

    @pytest.mark.asyncio
    async def test_rechazar_lote_cancela_pendientes(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        result = await ComunicacionesService.rechazar_lote(db_session, confirm_resp.lote_id, mock_user_approval)
        assert result.cancelados == 1

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant_with_approval.id)
        assert comunicaciones[0].estado == ComunicacionEstado.CANCELADO.value

    @pytest.mark.asyncio
    async def test_approve_already_enviando_no_effect(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant_with_approval.id,
            enviado_por=mock_user_approval.id,
            materia_id=test_materia_approval.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.ENVIANDO.value,
            lote_id=uuid.uuid4(),
            lote_aprobado=True,
        )
        db_session.add(c)
        await db_session.commit()

        result = await ComunicacionesService.aprobar_individual(db_session, c.id, mock_user_approval)
        assert result.estado == ComunicacionEstado.ENVIANDO.value

    @pytest.mark.asyncio
    async def test_approval_audit_log(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        await ComunicacionesService.aprobar_lote(db_session, confirm_resp.lote_id, mock_user_approval)

        stmt = select(AuditLog).where(AuditLog.action == "COMUNICACION_APROBAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Task 18: Cancel Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancel:

    @pytest.mark.asyncio
    async def test_cancel_individual_from_pendiente_to_cancelado(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant.id)
        target_id = comunicaciones[0].id

        result = await ComunicacionesService.cancelar_individual(db_session, target_id, mock_user)
        assert result.estado == ComunicacionEstado.CANCELADO.value

        updated = await repo.get_by_lote(confirm_resp.lote_id, test_tenant.id)
        assert updated[0].estado == ComunicacionEstado.CANCELADO.value

    @pytest.mark.asyncio
    async def test_cancel_from_enviando_fails(
        self, db_session, test_tenant, test_materia, mock_user
    ):
        c = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test",
            cuerpo="Cuerpo",
            estado=ComunicacionEstado.ENVIANDO.value,
        )
        db_session.add(c)
        await db_session.commit()

        result = await ComunicacionesService.cancelar_individual(db_session, c.id, mock_user)
        assert result.estado == ComunicacionEstado.ENVIANDO.value

    @pytest.mark.asyncio
    async def test_cancel_audit_log(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        repo = ComunicacionesRepository(db_session)
        comunicaciones = await repo.get_by_lote(confirm_resp.lote_id, test_tenant.id)

        await ComunicacionesService.cancelar_individual(db_session, comunicaciones[0].id, mock_user)

        stmt = select(AuditLog).where(AuditLog.action == "COMUNICACION_CANCELAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Additional: Panel / Lotes Query Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuery:

    @pytest.mark.asyncio
    async def test_get_lotes_returns_summary(
        self, db_session, test_tenant, test_materia, test_entrada_padron, test_entrada_padron2, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id, test_entrada_padron2.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        lotes_resp = await ComunicacionesService.get_lotes(db_session, test_materia.id, mock_user)
        assert lotes_resp.total >= 1
        assert len(lotes_resp.lotes) >= 1
        assert lotes_resp.lotes[0].total == 2
        assert lotes_resp.lotes[0].pendientes == 2

    @pytest.mark.asyncio
    async def test_get_lote_detail(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        detalle = await ComunicacionesService.get_lote_detalle(db_session, confirm_resp.lote_id, mock_user)
        assert detalle.lote.lote_id == confirm_resp.lote_id
        assert len(detalle.comunicaciones) == 1
        assert detalle.comunicaciones[0].asunto == "Test"

    @pytest.mark.asyncio
    async def test_estados_panel(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        panel = await ComunicacionesService.get_estados_panel(db_session, test_materia.id, mock_user)
        assert len(panel.items) >= 1
        panel_materia = next((p for p in panel.items if p.materia_id == test_materia.id), None)
        assert panel_materia is not None
        assert panel_materia.pendientes >= 1
        assert panel_materia.materia_nombre == "Matemática"


# ═══════════════════════════════════════════════════════════════════════════════
# Additional: Pendientes Elegibles Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPendientesElegibles:

    @pytest.mark.asyncio
    async def test_sin_aprobacion_todos_pendientes_elegibles(
        self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user)
        await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user)

        repo = ComunicacionesRepository(db_session)
        elegibles = await repo.get_pendientes_elegibles(test_tenant.id)
        assert len(elegibles) == 1

    @pytest.mark.asyncio
    async def test_con_aprobacion_pendientes_no_elegibles_sin_aprobar(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        repo = ComunicacionesRepository(db_session)
        elegibles = await repo.get_pendientes_elegibles(test_tenant_with_approval.id)
        assert len(elegibles) == 0

    @pytest.mark.asyncio
    async def test_con_aprobacion_aprobados_son_elegibles(
        self, db_session, test_tenant_with_approval, test_materia_approval, test_entrada_padron_approval, mock_user_approval
    ):
        preview_req = PreviewRequest(
            destinatarios=[test_entrada_padron_approval.id],
            asunto="Test",
            cuerpo="Cuerpo",
            materia_id=test_materia_approval.id,
        )
        preview_resp = await ComunicacionesService.preview(db_session, preview_req, mock_user_approval)
        confirm_resp = await ComunicacionesService.confirm(db_session, ConfirmRequest(preview_token=preview_resp.preview_token), mock_user_approval)

        await ComunicacionesService.aprobar_lote(db_session, confirm_resp.lote_id, mock_user_approval)

        repo = ComunicacionesRepository(db_session)
        elegibles = await repo.get_pendientes_elegibles(test_tenant_with_approval.id)
        assert len(elegibles) == 0
