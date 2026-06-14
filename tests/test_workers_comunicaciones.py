import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import Usuario
from app.models.materia import Materia
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.repositories.comunicaciones import ComunicacionesRepository

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
async def tenant_sin_aprobacion(db_session):
    t = Tenant(id=uuid.uuid4(), name="Sin Aprob", requiere_aprobacion=False)
    db_session.add(t)
    await db_session.commit()
    return t


@pytest_asyncio.fixture
async def tenant_con_aprobacion(db_session):
    t = Tenant(id=uuid.uuid4(), name="Con Aprob", requiere_aprobacion=True)
    db_session.add(t)
    await db_session.commit()
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session):
    t = Tenant(id=uuid.uuid4(), name="Tenant B", requiere_aprobacion=False)
    db_session.add(t)
    await db_session.commit()
    return t


async def _crear_comunicacion(db, tenant_id, estado=ComunicacionEstado.PENDIENTE.value, lote_aprobado=False):
    usuario = Usuario(id=uuid.uuid4(), tenant_id=tenant_id, email=f"env_{uuid.uuid4()}@t.com", dni="0", cuil="0")
    db.add(usuario)
    materia = Materia(id=uuid.uuid4(), tenant_id=tenant_id, name="M", code="M", is_active=True)
    db.add(materia)
    await db.flush()
    c = Comunicacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario="alumno@test.com",
        asunto="Test",
        cuerpo="Cuerpo",
        estado=estado,
        lote_id=uuid.uuid4(),
        lote_aprobado=lote_aprobado,
    )
    db.add(c)
    await db.commit()
    return c


class TestWorkerProcessPending:

    @pytest.mark.asyncio
    async def test_procesa_pendiente_a_enviado(self, db_session, tenant_sin_aprobacion):
        """Worker processes Pendiente → Enviado when send succeeds."""
        await _crear_comunicacion(db_session, tenant_sin_aprobacion.id)

        from app.workers.comunicaciones import process_pending_messages

        send_mock = AsyncMock(return_value=True)
        sent, failed = await process_pending_messages(
            db=db_session,
            tenant_id=tenant_sin_aprobacion.id,
            send_func=send_mock,
        )

        assert sent == 1
        assert failed == 0
        send_mock.assert_awaited_once()

        repo = ComunicacionesRepository(db_session)
        elegibles = await repo.get_pendientes_elegibles(tenant_sin_aprobacion.id)
        assert len(elegibles) == 0

        from sqlalchemy import select as sa_select
        stmt = sa_select(Comunicacion)
        result = await db_session.execute(stmt)
        coms = list(result.scalars().all())
        assert len(coms) == 1
        assert coms[0].estado == ComunicacionEstado.ENVIADO.value
        assert coms[0].enviado_at is not None

    @pytest.mark.asyncio
    async def test_maneja_error_smtp_a_error(self, db_session, tenant_sin_aprobacion):
        """Worker sets Error when send fails."""
        await _crear_comunicacion(db_session, tenant_sin_aprobacion.id)

        from app.workers.comunicaciones import process_pending_messages

        send_mock = AsyncMock(return_value=False)
        sent, failed = await process_pending_messages(
            db=db_session,
            tenant_id=tenant_sin_aprobacion.id,
            send_func=send_mock,
        )

        assert sent == 0
        assert failed == 1

        from sqlalchemy import select as sa_select
        stmt = sa_select(Comunicacion)
        result = await db_session.execute(stmt)
        coms = list(result.scalars().all())
        assert len(coms) == 1
        assert coms[0].estado == ComunicacionEstado.ERROR.value

    @pytest.mark.asyncio
    async def test_reintenta_hasta_max_retries(self, db_session, tenant_sin_aprobacion):
        """Worker retries on failure, succeeds on 3rd attempt."""
        await _crear_comunicacion(db_session, tenant_sin_aprobacion.id)

        from app.workers.comunicaciones import process_pending_messages

        call_count = 0

        async def flaky_send(destinatario, asunto, cuerpo):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return False
            return True

        sent, failed = await process_pending_messages(
            db=db_session,
            tenant_id=tenant_sin_aprobacion.id,
            send_func=flaky_send,
        )

        assert call_count == 3
        assert sent == 1
        assert failed == 0

        from sqlalchemy import select as sa_select
        stmt = sa_select(Comunicacion)
        result = await db_session.execute(stmt)
        coms = list(result.scalars().all())
        assert coms[0].estado == ComunicacionEstado.ENVIADO.value

    @pytest.mark.asyncio
    async def test_skip_no_elegibles_con_aprobacion(self, db_session, tenant_con_aprobacion):
        """Worker skips messages that need approval but aren't approved."""
        await _crear_comunicacion(
            db_session,
            tenant_con_aprobacion.id,
            lote_aprobado=False,
        )

        from app.workers.comunicaciones import process_pending_messages

        send_mock = AsyncMock(return_value=True)
        sent, failed = await process_pending_messages(
            db=db_session,
            tenant_id=tenant_con_aprobacion.id,
            send_func=send_mock,
        )

        assert sent == 0
        assert failed == 0
        send_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_cancelado(self, db_session, tenant_sin_aprobacion):
        """Worker skips Cancelado messages."""
        await _crear_comunicacion(
            db_session,
            tenant_sin_aprobacion.id,
            estado=ComunicacionEstado.CANCELADO.value,
        )

        from app.workers.comunicaciones import process_pending_messages

        send_mock = AsyncMock(return_value=True)
        sent, failed = await process_pending_messages(
            db=db_session,
            tenant_id=tenant_sin_aprobacion.id,
            send_func=send_mock,
        )

        assert sent == 0
        assert failed == 0
        send_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_aislamiento_entre_tenants(self, db_session, tenant_sin_aprobacion, tenant_b):
        """Worker only processes messages for the given tenant."""
        await _crear_comunicacion(db_session, tenant_sin_aprobacion.id)
        await _crear_comunicacion(db_session, tenant_b.id)

        from app.workers.comunicaciones import process_pending_messages

        send_mock = AsyncMock(return_value=True)
        sent, failed = await process_pending_messages(
            db=db_session,
            tenant_id=tenant_sin_aprobacion.id,
            send_func=send_mock,
        )

        assert sent == 1
        assert failed == 0
        send_mock.assert_awaited_once()

        repo = ComunicacionesRepository(db_session)
        elegibles_b = await repo.get_pendientes_elegibles(tenant_b.id)
        assert len(elegibles_b) == 1
        assert elegibles_b[0].estado == ComunicacionEstado.PENDIENTE.value

    @pytest.mark.asyncio
    async def test_send_email_function(self, db_session, tenant_sin_aprobacion):
        """Test that send_email builds and sends via SMTP (mocked)."""
        from app.workers.comunicaciones import send_email

        with patch("app.workers.comunicaciones.smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await send_email("alumno@test.com", "Asunto", "Cuerpo")

            assert result is True
            mock_smtp.assert_called_once()
            args, _ = mock_smtp.call_args
            assert args[0] == "localhost"

    @pytest.mark.asyncio
    async def test_send_email_failure(self):
        """Test that send_email returns False on SMTP error."""
        from app.workers.comunicaciones import send_email

        with patch("app.workers.comunicaciones.smtplib.SMTP", side_effect=ConnectionError("refused")):
            result = await send_email("alumno@test.com", "Asunto", "Cuerpo")
            assert result is False
