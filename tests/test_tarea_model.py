import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.tarea import Tarea, ComentarioTarea, EstadoTarea


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys=ON"))
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
        email="user@test.com",
        hashed_password="x",
        _dni="12345678",
        _cuil="20-12345678-9",
    )
    db_session.add(usuario)
    await db_session.commit()
    return usuario


@pytest_asyncio.fixture
async def test_usuario2(db_session, test_tenant):
    usuario = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="user2@test.com",
        hashed_password="x",
        _dni="87654321",
        _cuil="20-87654321-9",
    )
    db_session.add(usuario)
    await db_session.commit()
    return usuario


@pytest_asyncio.fixture
async def test_auth_user(db_session, test_tenant):
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="auth@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_materia(db_session, test_tenant):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="MAT101")
    db_session.add(materia)
    await db_session.commit()
    return materia


class TestEstadoTarea:

    @pytest.mark.asyncio
    async def test_enum_values(self):
        assert EstadoTarea.PENDIENTE.value == "Pendiente"
        assert EstadoTarea.EN_PROGRESO.value == "En progreso"
        assert EstadoTarea.RESUELTA.value == "Resuelta"
        assert EstadoTarea.CANCELADA.value == "Cancelada"


class TestTareaModel:

    @pytest.mark.asyncio
    async def test_create_tarea_defaults(self, db_session, test_tenant, test_usuario, test_auth_user):
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Revisar planificaciones",
        )
        db_session.add(tarea)
        await db_session.commit()

        assert tarea.estado == EstadoTarea.PENDIENTE.value
        assert tarea.materia_id is None
        assert tarea.contexto_id is None
        assert tarea.id is not None

    @pytest.mark.asyncio
    async def test_create_tarea_all_fields(self, db_session, test_tenant, test_usuario, test_auth_user, test_materia):
        contexto_id = uuid.uuid4()
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            estado=EstadoTarea.EN_PROGRESO.value,
            descripcion="Tarea completa",
            contexto_id=contexto_id,
        )
        db_session.add(tarea)
        await db_session.commit()

        assert tarea.materia_id == test_materia.id
        assert tarea.asignado_a == test_usuario.id
        assert tarea.asignado_por == test_auth_user.id
        assert tarea.estado == EstadoTarea.EN_PROGRESO.value
        assert tarea.descripcion == "Tarea completa"
        assert tarea.contexto_id == contexto_id

    @pytest.mark.asyncio
    async def test_tarea_nullable_materia_id(self, db_session, test_tenant, test_usuario, test_auth_user):
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Sin materia",
        )
        db_session.add(tarea)
        await db_session.commit()

        assert tarea.materia_id is None
        assert tarea.descripcion == "Sin materia"

    @pytest.mark.asyncio
    async def test_tarea_soft_delete(self, db_session, test_tenant, test_usuario, test_auth_user):
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="A soft-delete",
        )
        db_session.add(tarea)
        await db_session.commit()
        assert tarea.deleted_at is None

        tarea.deleted_at = datetime(2026, 6, 12)
        await db_session.commit()

        assert tarea.deleted_at is not None

    @pytest.mark.asyncio
    async def test_tarea_tenant_isolation(self, db_session, test_tenant, test_usuario, test_auth_user):
        other_tenant = Tenant(id=uuid.uuid4(), name="Other Tenant")
        db_session.add(other_tenant)
        await db_session.commit()

        t1 = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Tarea tenant 1",
        )
        t2 = Tarea(
            id=uuid.uuid4(),
            tenant_id=other_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Tarea tenant 2",
        )
        db_session.add_all([t1, t2])
        await db_session.commit()

        result = await db_session.execute(
            select(Tarea).where(Tarea.tenant_id == test_tenant.id)
        )
        tareas = result.scalars().all()
        assert len(tareas) == 1
        assert tareas[0].descripcion == "Tarea tenant 1"


class TestComentarioTareaModel:

    @pytest.mark.asyncio
    async def test_create_comentario(self, db_session, test_tenant, test_usuario, test_auth_user):
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Con comentario",
        )
        db_session.add(tarea)
        await db_session.commit()

        comentario = ComentarioTarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            tarea_id=tarea.id,
            autor_id=test_auth_user.id,
            texto="Este es un comentario",
        )
        db_session.add(comentario)
        await db_session.commit()

        assert comentario.id is not None
        assert comentario.tarea_id == tarea.id
        assert comentario.autor_id == test_auth_user.id
        assert comentario.texto == "Este es un comentario"
        assert comentario.created_at is not None

    @pytest.mark.asyncio
    async def test_comentario_cascade_on_tarea_delete(self, db_session, test_tenant, test_usuario, test_auth_user):
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Cascade test",
        )
        db_session.add(tarea)
        await db_session.commit()

        comentario = ComentarioTarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            tarea_id=tarea.id,
            autor_id=test_auth_user.id,
            texto="Se borrará con la tarea",
        )
        db_session.add(comentario)
        await db_session.commit()

        await db_session.delete(tarea)
        await db_session.commit()

        result = await db_session.execute(
            select(ComentarioTarea).where(ComentarioTarea.id == comentario.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_comentario_soft_delete(self, db_session, test_tenant, test_usuario, test_auth_user):
        tarea = Tarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            asignado_a=test_usuario.id,
            asignado_por=test_auth_user.id,
            descripcion="Soft delete comment",
        )
        db_session.add(tarea)
        await db_session.commit()

        comentario = ComentarioTarea(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            tarea_id=tarea.id,
            autor_id=test_auth_user.id,
            texto="A soft-delete",
        )
        db_session.add(comentario)
        await db_session.commit()
        assert comentario.deleted_at is None

        comentario.deleted_at = datetime(2026, 6, 12)
        await db_session.commit()

        assert comentario.deleted_at is not None
