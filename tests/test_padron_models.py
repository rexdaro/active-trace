import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.padron import VersionPadron, EntradaPadron

os.environ["ENCRYPTION_KEY"] = "test-key-32-chars-long-for-encryption!!"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


class TestVersionPadronModel:

    @pytest.mark.asyncio
    async def test_version_padron_fields(self, db_session):
        version = VersionPadron(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            archivo_nombre="alumnos.xlsx",
            archivo_hash="abc123def456",
            origen="Archivo",
            cargado_por=uuid.uuid4(),
            activa=True,
        )
        db_session.add(version)
        await db_session.commit()

        assert version.id is not None
        assert version.archivo_nombre == "alumnos.xlsx"
        assert version.origen == "Archivo"
        assert version.activa is True
        assert hasattr(version, "created_at")
        assert hasattr(version, "updated_at")

    @pytest.mark.asyncio
    async def test_version_padron_defaults(self, db_session):
        version = VersionPadron(
            tenant_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            archivo_nombre="test.csv",
            archivo_hash="hash",
            origen="MoodleWS",
            cargado_por=uuid.uuid4(),
        )
        db_session.add(version)
        await db_session.commit()

        assert version.activa is True


class TestEntradaPadronModel:

    @pytest.mark.asyncio
    async def test_entrada_padron_fields(self, db_session):
        version = VersionPadron(
            tenant_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            archivo_nombre="test.xlsx",
            archivo_hash="hash1",
            origen="Archivo",
            cargado_por=uuid.uuid4(),
        )
        db_session.add(version)
        await db_session.commit()

        entrada = EntradaPadron(
            version_id=version.id,
            tenant_id=version.tenant_id,
            email="alumno@test.com",
            nombre="Juan",
            apellidos="Pérez",
            comision="A",
            regional="CABA",
        )
        db_session.add(entrada)
        await db_session.commit()

        assert entrada.id is not None
        assert entrada.version_id == version.id
        assert entrada.nombre == "Juan"
        assert entrada.apellidos == "Pérez"
        assert entrada.email == "alumno@test.com"
        assert entrada.comision == "A"
        assert entrada.regional == "CABA"
        assert entrada.usuario_id is None

    @pytest.mark.asyncio
    async def test_entrada_padron_email_encryption(self, db_session):
        version = VersionPadron(
            tenant_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            archivo_nombre="test.xlsx",
            archivo_hash="hash2",
            origen="Archivo",
            cargado_por=uuid.uuid4(),
        )
        db_session.add(version)
        await db_session.commit()

        entrada = EntradaPadron(
            version_id=version.id,
            tenant_id=version.tenant_id,
            email="secreto@test.com",
            nombre="Secreto",
            apellidos="User",
        )
        db_session.add(entrada)
        await db_session.commit()

        assert entrada.email == "secreto@test.com"
        assert entrada._email != "secreto@test.com"
        assert entrada._email != entrada.email
