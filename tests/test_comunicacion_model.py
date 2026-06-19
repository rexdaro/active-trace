import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.core.security import encrypt, decrypt

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
        email="teacher@test.com",
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
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="MAT101", is_active=True)
    db_session.add(materia)
    await db_session.commit()
    return materia


class TestComunicacionModel:

    @pytest.mark.asyncio
    async def test_create_comunicacion_defaults(self, db_session, test_tenant, mock_user, test_materia):
        comunicacion = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Recordatorio",
            cuerpo="Este es un recordatorio.",
        )
        db_session.add(comunicacion)
        await db_session.commit()

        assert comunicacion.estado == ComunicacionEstado.PENDIENTE
        assert comunicacion.lote_aprobado is False
        assert comunicacion.destinatario == "alumno@test.com"

    @pytest.mark.asyncio
    async def test_encrypted_email(self, db_session, test_tenant, mock_user, test_materia):
        original_email = "alumno@test.com"
        comunicacion = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario=original_email,
            asunto="Prueba",
            cuerpo="Cuerpo de prueba.",
        )
        db_session.add(comunicacion)
        await db_session.commit()

        raw_value = comunicacion._destinatario
        assert raw_value != original_email
        assert comunicacion.destinatario == original_email

        comunicacion.destinatario = "nuevo@test.com"
        await db_session.commit()
        assert comunicacion._destinatario != "nuevo@test.com"
        assert comunicacion.destinatario == "nuevo@test.com"

    @pytest.mark.asyncio
    async def test_estado_enum_values(self):
        assert ComunicacionEstado.PENDIENTE.value == "Pendiente"
        assert ComunicacionEstado.ENVIANDO.value == "Enviando"
        assert ComunicacionEstado.ENVIADO.value == "Enviado"
        assert ComunicacionEstado.ERROR.value == "Error"
        assert ComunicacionEstado.CANCELADO.value == "Cancelado"

    @pytest.mark.asyncio
    async def test_tenant_requiere_aprobacion_defaults(self, db_session):
        tenant = Tenant(id=uuid.uuid4(), name="Test Tenant Defaults")
        db_session.add(tenant)
        await db_session.commit()

        assert tenant.requiere_aprobacion is False

    @pytest.mark.asyncio
    async def test_lote_nullable(self, db_session, test_tenant, mock_user, test_materia):
        comunicacion = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Sin lote",
            cuerpo="Sin lote asociado.",
        )
        db_session.add(comunicacion)
        await db_session.commit()

        assert comunicacion.lote_id is None
        assert comunicacion.enviado_at is None

    @pytest.mark.asyncio
    async def test_set_enviado_at(self, db_session, test_tenant, mock_user, test_materia):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        comunicacion = Comunicacion(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            enviado_por=mock_user.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Enviado",
            cuerpo="Enviado body.",
            estado=ComunicacionEstado.ENVIADO,
            enviado_at=now,
        )
        db_session.add(comunicacion)
        await db_session.commit()

        assert comunicacion.estado == ComunicacionEstado.ENVIADO
        assert comunicacion.enviado_at is not None
