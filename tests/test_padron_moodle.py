import pytest
import pytest_asyncio
import uuid
import os
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.padron import VersionPadron
from app.repositories.padron import PadronRepository
from app.integrations.moodle_ws import MoodleWSService
from app.services.audit import AuditService
from fastapi import HTTPException

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
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Moodle Tenant",
        moodle_ws_url="https://moodle.example.com",
        moodle_token="test-token-123",
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant


@pytest_asyncio.fixture
async def mock_user(db_session, test_tenant):
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
async def test_materia(db_session, test_tenant):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="101", is_active=True)
    db_session.add(materia)
    await db_session.commit()
    return materia


# ─── Task 20: Moodle WS mock ─────────────────────────────────────────────────

class TestMoodleWSMock:

    @pytest.mark.asyncio
    async def test_get_tenant_config(self, db_session, test_tenant):
        url, token = await MoodleWSService._get_tenant_config(db_session, test_tenant.id)
        assert url == "https://moodle.example.com"
        assert token == "test-token-123"

    @pytest.mark.asyncio
    async def test_get_tenant_config_no_config(self, db_session):
        other_tenant = Tenant(id=uuid.uuid4(), name="No Moodle")
        db_session.add(other_tenant)
        await db_session.commit()

        url, token = await MoodleWSService._get_tenant_config(db_session, other_tenant.id)
        assert url is None
        assert token is None

    @pytest.mark.asyncio
    async def test_sync_creates_version_origen_moodle(self, db_session, mock_user, test_tenant, test_materia):
        participants_data = [
            {"firstname": "Ana", "lastname": "López", "email": "ana@test.com", "id": 1},
            {"firstname": "Luis", "lastname": "García", "email": "luis@test.com", "id": 2},
        ]

        with patch.object(MoodleWSService, '_call_moodle', new=AsyncMock(return_value=participants_data)):
            result = await MoodleWSService.sync_from_moodle(db_session, mock_user, test_materia.id)

        assert result["status"] == "completed"
        assert result["materias_procesadas"] == 1

        repo = PadronRepository(db_session)
        versiones = await repo.get_versiones_materia(test_materia.id, test_tenant.id)
        assert len(versiones) == 1
        assert versiones[0].origen == "MoodleWS"

    @pytest.mark.asyncio
    async def test_sync_sin_config_retorna_skipped(self, db_session, mock_user, test_materia):
        mock_user.tenant_id = uuid.uuid4()
        result = await MoodleWSService.sync_from_moodle(db_session, mock_user, test_materia.id)
        assert result["status"] == "skipped"


# ─── Task 21: Fallback 502 ─────────────────────────────────────────────────

class TestMoodleFallback502:

    @pytest.mark.asyncio
    async def test_call_moodle_retry_then_502(self):
        import httpx
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value = mock_instance

            with pytest.raises(HTTPException) as exc:
                await MoodleWSService._call_moodle("test_func", "https://example.com", "token")

            assert exc.value.status_code == 502

    @pytest.mark.asyncio
    async def test_sync_moodle_no_disponible(self, db_session, mock_user, test_tenant, test_materia):
        with patch.object(MoodleWSService, '_call_moodle', new=AsyncMock(side_effect=HTTPException(
            status_code=502, detail="Moodle WS no disponible después de 3 intentos: Connection refused"
        ))):
            result = await MoodleWSService.sync_from_moodle(db_session, mock_user, test_materia.id)

        assert result["status"] == "completed"
        assert result["materias_procesadas"] == 0
        assert len(result["errores"]) == 1
        assert "502" in result["errores"][0] or "Connection refused" in result["errores"][0]

    @pytest.mark.asyncio
    async def test_call_moodle_exitoso(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_response = MagicMock()
            mock_response.json.return_value = {"users": [{"id": 1, "firstname": "Test"}]}
            mock_response.raise_for_status.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await MoodleWSService._call_moodle("core_enrol_get_enrolled_users", "https://example.com", "token")
            assert result == {"users": [{"id": 1, "firstname": "Test"}]}
