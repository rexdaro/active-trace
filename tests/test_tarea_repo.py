import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.tarea import Tarea, ComentarioTarea, EstadoTarea
from app.repositories.tareas import TareaRepository
from app.schemas.tarea import TareaListParams


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
async def test_user(db_session, test_tenant):
    user = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        _email="user@test.com",
        _dni="12345678",
        _cuil="20-12345678-9",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_user2(db_session, test_tenant):
    user = Usuario(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        _email="user2@test.com",
        _dni="87654321",
        _cuil="20-87654321-9",
    )
    db_session.add(user)
    await db_session.commit()
    return user


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


@pytest_asyncio.fixture
async def repo(db_session):
    return TareaRepository(db_session)


@pytest.mark.asyncio
class TestTareaRepo:

    async def test_create_tarea(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Tarea de prueba",
            "estado": EstadoTarea.PENDIENTE.value,
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        assert tarea.id is not None
        assert tarea.descripcion == "Tarea de prueba"
        assert tarea.estado == EstadoTarea.PENDIENTE.value
        assert tarea.asignado_a == test_user.id
        assert tarea.asignado_por == test_auth_user.id
        assert tarea.tenant_id == test_tenant.id

        fetched = await repo.get(tarea.id, test_tenant.id)
        assert fetched is not None
        assert fetched.descripcion == "Tarea de prueba"

    async def test_get_tarea_not_found(self, repo, db_session, test_tenant):
        fetched = await repo.get(uuid.uuid4(), test_tenant.id)
        assert fetched is None

    async def test_get_tarea_other_tenant(self, repo, db_session, test_tenant, test_user, test_auth_user):
        other_tenant = Tenant(id=uuid.uuid4(), name="Other")
        db_session.add(other_tenant)
        await db_session.commit()

        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Tarea in other tenant",
        }
        tarea = await repo.create(data, other_tenant.id)
        await db_session.commit()

        fetched = await repo.get(tarea.id, test_tenant.id)
        assert fetched is None

    async def test_update_tarea(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Original",
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        updated = await repo.update(tarea, {"descripcion": "Modificada", "estado": EstadoTarea.EN_PROGRESO.value})
        await db_session.commit()

        assert updated.descripcion == "Modificada"
        assert updated.estado == EstadoTarea.EN_PROGRESO.value

        fetched = await repo.get(tarea.id, test_tenant.id)
        assert fetched.descripcion == "Modificada"
        assert fetched.estado == EstadoTarea.EN_PROGRESO.value

    async def test_delete_tarea_soft(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "A eliminar",
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        await repo.delete(tarea.id, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get(tarea.id, test_tenant.id)
        assert fetched is None

    async def test_list_by_asignado(self, repo, db_session, test_tenant, test_user, test_auth_user):
        for i in range(3):
            data = {
                "asignado_a": test_user.id,
                "asignado_por": test_auth_user.id,
                "descripcion": f"Tarea {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list_by_asignado(test_user.id, test_tenant.id, 0, 10)
        assert total == 3
        assert len(items) == 3

        items2, total2 = await repo.list_by_asignado(uuid.uuid4(), test_tenant.id, 0, 10)
        assert total2 == 0
        assert len(items2) == 0

    async def test_list_by_asignado_pagination(self, repo, db_session, test_tenant, test_user, test_auth_user):
        for i in range(5):
            data = {
                "asignado_a": test_user.id,
                "asignado_por": test_auth_user.id,
                "descripcion": f"Tarea {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list_by_asignado(test_user.id, test_tenant.id, 0, 2)
        assert total == 5
        assert len(items) == 2

    async def test_list_all_no_filters(self, repo, db_session, test_tenant, test_user, test_user2, test_auth_user):
        for i in range(3):
            data = {
                "asignado_a": test_user.id if i % 2 == 0 else test_user2.id,
                "asignado_por": test_auth_user.id,
                "descripcion": f"Tarea {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list_all(test_tenant.id, TareaListParams(), 0, 10)
        assert total == 3
        assert len(items) == 3

    async def test_list_all_filter_by_estado(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data1 = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Pendiente",
            "estado": EstadoTarea.PENDIENTE.value,
        }
        data2 = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "En progreso",
            "estado": EstadoTarea.EN_PROGRESO.value,
        }
        await repo.create(data1, test_tenant.id)
        await repo.create(data2, test_tenant.id)
        await db_session.commit()

        params = TareaListParams(estado=EstadoTarea.EN_PROGRESO.value)
        items, total = await repo.list_all(test_tenant.id, params, 0, 10)
        assert total == 1
        assert items[0].descripcion == "En progreso"

    async def test_list_all_filter_by_asignado(self, repo, db_session, test_tenant, test_user, test_user2, test_auth_user):
        for i in range(2):
            data = {
                "asignado_a": test_user.id,
                "asignado_por": test_auth_user.id,
                "descripcion": f"User1 tarea {i}",
            }
            await repo.create(data, test_tenant.id)
        data = {
            "asignado_a": test_user2.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "User2 tarea",
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        params = TareaListParams(asignado_a=test_user.id)
        items, total = await repo.list_all(test_tenant.id, params, 0, 10)
        assert total == 2
        assert all(i.asignado_a == test_user.id for i in items)

    async def test_list_all_filter_by_materia(self, repo, db_session, test_tenant, test_user, test_auth_user, test_materia):
        data1 = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Con materia",
            "materia_id": test_materia.id,
        }
        data2 = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Sin materia",
        }
        await repo.create(data1, test_tenant.id)
        await repo.create(data2, test_tenant.id)
        await db_session.commit()

        params = TareaListParams(materia_id=test_materia.id)
        items, total = await repo.list_all(test_tenant.id, params, 0, 10)
        assert total == 1
        assert items[0].descripcion == "Con materia"

    async def test_list_all_pagination(self, repo, db_session, test_tenant, test_user, test_auth_user):
        for i in range(5):
            data = {
                "asignado_a": test_user.id,
                "asignado_por": test_auth_user.id,
                "descripcion": f"Tarea {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list_all(test_tenant.id, TareaListParams(), 0, 2)
        assert total == 5
        assert len(items) == 2

    async def test_soft_deleted_hidden_from_list(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Visible",
        }
        tarea = await repo.create(data, test_tenant.id)
        data2 = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Oculto",
        }
        tarea2 = await repo.create(data2, test_tenant.id)
        await db_session.commit()

        await repo.delete(tarea2.id, test_tenant.id)
        await db_session.commit()

        items, total = await repo.list_all(test_tenant.id, TareaListParams(), 0, 10)
        assert total == 1
        assert items[0].descripcion == "Visible"

    async def test_count_by_asignado(self, repo, db_session, test_tenant, test_user, test_auth_user):
        for i in range(3):
            data = {
                "asignado_a": test_user.id,
                "asignado_por": test_auth_user.id,
                "descripcion": f"Tarea {i}",
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        count = await repo.count_by_asignado(test_user.id, test_tenant.id)
        assert count == 3


@pytest.mark.asyncio
class TestComentarioTareaRepo:

    async def test_create_and_list_comentarios(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Con comentarios",
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        c1 = await repo.create_comentario({
            "tarea_id": tarea.id,
            "autor_id": test_auth_user.id,
            "texto": "Primer comentario",
        }, test_tenant.id)
        c2 = await repo.create_comentario({
            "tarea_id": tarea.id,
            "autor_id": test_auth_user.id,
            "texto": "Segundo comentario",
        }, test_tenant.id)
        await db_session.commit()

        assert c1.id is not None
        assert c1.texto == "Primer comentario"

        comentarios = await repo.list_comentarios(tarea.id, test_tenant.id)
        assert len(comentarios) == 2

    async def test_get_comentario(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Get comentario",
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        c = await repo.create_comentario({
            "tarea_id": tarea.id,
            "autor_id": test_auth_user.id,
            "texto": "Encontrame",
        }, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get_comentario(c.id, test_tenant.id)
        assert fetched is not None
        assert fetched.texto == "Encontrame"

    async def test_delete_comentario(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Borrar comentario",
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        c = await repo.create_comentario({
            "tarea_id": tarea.id,
            "autor_id": test_auth_user.id,
            "texto": "A borrar",
        }, test_tenant.id)
        await db_session.commit()

        await repo.delete_comentario(c.id, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get_comentario(c.id, test_tenant.id)
        assert fetched is None

    async def test_list_comentarios_excludes_soft_deleted(self, repo, db_session, test_tenant, test_user, test_auth_user):
        data = {
            "asignado_a": test_user.id,
            "asignado_por": test_auth_user.id,
            "descripcion": "Comentarios",
        }
        tarea = await repo.create(data, test_tenant.id)
        await db_session.commit()

        c1 = await repo.create_comentario({
            "tarea_id": tarea.id,
            "autor_id": test_auth_user.id,
            "texto": "Visible",
        }, test_tenant.id)
        c2 = await repo.create_comentario({
            "tarea_id": tarea.id,
            "autor_id": test_auth_user.id,
            "texto": "Oculto",
        }, test_tenant.id)
        await db_session.commit()

        await repo.delete_comentario(c2.id, test_tenant.id)
        await db_session.commit()

        comentarios = await repo.list_comentarios(tarea.id, test_tenant.id)
        assert len(comentarios) == 1
        assert comentarios[0].texto == "Visible"
