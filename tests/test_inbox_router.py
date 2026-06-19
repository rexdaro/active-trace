import pytest
import pytest_asyncio
import uuid
import os

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.inbox import router as inbox_router
from app.core.rbac import get_current_user
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.mensaje_interno import MensajeInterno
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select


class TestInboxRouterSinAuth:

    def setup_method(self):
        self.app = FastAPI()
        self.app.include_router(inbox_router)
        self.client = TestClient(self.app)

    def test_list_recibidos_sin_token_returns_401(self):
        response = self.client.get("/api/v1/inbox")
        assert response.status_code == 401

    def test_list_enviados_sin_token_returns_401(self):
        response = self.client.get("/api/v1/inbox/enviados")
        assert response.status_code == 401

    def test_send_sin_token_returns_401(self):
        response = self.client.post("/api/v1/inbox", json={})
        assert response.status_code == 401

    def test_responder_sin_token_returns_401(self):
        response = self.client.post(f"/api/v1/inbox/{uuid.uuid4()}/responder", json={})
        assert response.status_code == 401

    def test_marcar_leido_sin_token_returns_401(self):
        response = self.client.put(f"/api/v1/inbox/{uuid.uuid4()}/leer")
        assert response.status_code == 401


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def integration_setup(db_session):
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db_session.add(tenant)

    import app.core.security as sec
    key = os.environ.get("ENCRYPTION_KEY", "dev-key")

    user_a = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="user_a@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    user_a._dni = sec.encrypt("11111111", key)
    user_a._cuil = sec.encrypt("20-11111111-1", key)
    db_session.add(user_a)

    user_b = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="user_b@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    user_b._dni = sec.encrypt("22222222", key)
    user_b._cuil = sec.encrypt("20-22222222-2", key)
    db_session.add(user_b)

    await db_session.commit()

    app = FastAPI()
    app.include_router(inbox_router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client, tenant, user_a, user_b, db_session


class TestInboxRouterIntegration:

    @pytest.mark.asyncio
    async def test_enviar_mensaje(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        payload = {
            "destinatario_id": str(user_b.id),
            "asunto": "Hola",
            "cuerpo": "Mensaje de prueba",
        }
        response = client.post(
            "/api/v1/inbox",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["asunto"] == "Hola"
        assert data["cuerpo"] == "Mensaje de prueba"
        assert data["remitente_id"] == str(user_a.id)
        assert data["destinatario_id"] == str(user_b.id)
        assert data["leido"] is False

    @pytest.mark.asyncio
    async def test_enviar_destinatario_inexistente_returns_404(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        fake_id = uuid.uuid4()
        payload = {
            "destinatario_id": str(fake_id),
            "asunto": "Test",
            "cuerpo": "No deberia llegar",
        }
        response = client.post(
            "/api/v1/inbox",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_listar_recibidos(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        msg = MensajeInterno(
            tenant_id=tenant.id,
            remitente_id=user_b.id,
            destinatario_id=user_a.id,
            asunto="Para A",
            cuerpo="Mensaje para user_a",
        )
        db.add(msg)
        await db.commit()

        response = client.get("/api/v1/inbox", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["asunto"] == "Para A"

    @pytest.mark.asyncio
    async def test_listar_enviados(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        msg = MensajeInterno(
            tenant_id=tenant.id,
            remitente_id=user_a.id,
            destinatario_id=user_b.id,
            asunto="De A para B",
            cuerpo="Enviado por user_a",
        )
        db.add(msg)
        await db.commit()

        response = client.get(
            "/api/v1/inbox/enviados",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["asunto"] == "De A para B"

    @pytest.mark.asyncio
    async def test_marcar_leido(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        msg = MensajeInterno(
            tenant_id=tenant.id,
            remitente_id=user_b.id,
            destinatario_id=user_a.id,
            asunto="No leido",
            cuerpo="Marcar como leido",
            leido=False,
        )
        db.add(msg)
        await db.commit()

        response = client.put(
            f"/api/v1/inbox/{msg.id}/leer",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["leido"] is True

    @pytest.mark.asyncio
    async def test_responder_hilo(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        msg = MensajeInterno(
            tenant_id=tenant.id,
            remitente_id=user_b.id,
            destinatario_id=user_a.id,
            asunto="Consulta",
            cuerpo="Tengo una duda",
        )
        db.add(msg)
        await db.commit()

        response = client.post(
            f"/api/v1/inbox/{msg.id}/responder",
            json={"cuerpo": "Claro, decime"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cuerpo"] == "Claro, decime"
        assert data["hilo_id"] is not None
        assert data["remitente_id"] == str(user_a.id)
        assert data["destinatario_id"] == str(user_b.id)

    @pytest.mark.asyncio
    async def test_responder_mensaje_inexistente_returns_404(self, integration_setup):
        client, tenant, user_a, user_b, db = integration_setup
        response = client.post(
            f"/api/v1/inbox/{uuid.uuid4()}/responder",
            json={"cuerpo": "Respuesta"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404
