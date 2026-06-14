import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso, SeveridadAviso
from app.models.user import Usuario
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.repositories.avisos import AvisoRepository
from app.schemas.aviso import AvisoListParams


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
async def repo(db_session):
    return AvisoRepository(db_session)


@pytest_asyncio.fixture
async def test_usuario(db_session, test_tenant):
    u = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"fix_{uuid.uuid4()}@t.com", dni="0", cuil="0")
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def test_materia(db_session, test_tenant):
    m = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="T", code="T", is_active=True)
    db_session.add(m)
    await db_session.commit()
    return m


@pytest_asyncio.fixture
async def test_carrera(db_session, test_tenant):
    c = Carrera(id=uuid.uuid4(), tenant_id=test_tenant.id, name="T", code="T", is_active=True)
    db_session.add(c)
    await db_session.commit()
    return c


@pytest_asyncio.fixture
async def test_cohorte(db_session, test_tenant, test_carrera):
    co = Cohorte(id=uuid.uuid4(), tenant_id=test_tenant.id, carrera_id=test_carrera.id, name="2025", is_active=True)
    db_session.add(co)
    await db_session.commit()
    return co


def utc_now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
class TestAvisoRepo:

    async def test_create_aviso(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Aviso importante",
            "cuerpo": "Cuerpo del aviso de prueba.",
            "alcance": AlcanceAviso.POR_ROL.value,
            "rol_destino": "PROFESOR",
            "severidad": SeveridadAviso.CRITICO.value,
            "inicio_en": utc_now(),
            "fin_en": utc_now() + timedelta(days=30),
            "orden": 5,
            "activo": True,
            "requiere_ack": True,
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        assert aviso.id is not None
        assert aviso.titulo == "Aviso importante"
        assert aviso.cuerpo == "Cuerpo del aviso de prueba."
        assert aviso.alcance == AlcanceAviso.POR_ROL.value
        assert aviso.rol_destino == "PROFESOR"
        assert aviso.severidad == SeveridadAviso.CRITICO.value
        assert aviso.orden == 5
        assert aviso.activo is True
        assert aviso.requiere_ack is True
        assert aviso.tenant_id == test_tenant.id

        fetched = await repo.get(aviso.id, test_tenant.id)
        assert fetched is not None
        assert fetched.titulo == "Aviso importante"

    async def test_create_aviso_minimal(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Aviso mínimo",
            "cuerpo": "Cuerpo mínimo.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now(),
            "fin_en": utc_now() + timedelta(days=7),
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        assert aviso.activo is True
        assert aviso.requiere_ack is False
        assert aviso.orden == 0
        assert aviso.severidad == SeveridadAviso.INFO.value

    async def test_list_visibles_global(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Global aviso",
            "cuerpo": "Visible para todos.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        visibles = await repo.list_visibles(test_tenant.id)
        assert len(visibles) == 1
        assert visibles[0].titulo == "Global aviso"

    async def test_list_visibles_filters_by_vigencia(self, repo, db_session, test_tenant):
        data_vencido = {
            "titulo": "Vencido",
            "cuerpo": "Ya venció.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=10),
            "fin_en": utc_now() - timedelta(days=1),
        }
        await repo.create(data_vencido, test_tenant.id)
        await db_session.commit()

        visibles = await repo.list_visibles(test_tenant.id)
        assert len(visibles) == 0

    async def test_list_visibles_filters_by_rol(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Solo profesores",
            "cuerpo": "Para PROFESOR.",
            "alcance": AlcanceAviso.POR_ROL.value,
            "rol_destino": "PROFESOR",
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        visibles = await repo.list_visibles(test_tenant.id, usuario_rol="PROFESOR")
        assert len(visibles) == 1

        visibles_otro = await repo.list_visibles(test_tenant.id, usuario_rol="ALUMNO")
        assert len(visibles_otro) == 0

    async def test_list_visibles_ordered_by_orden(self, repo, db_session, test_tenant):
        for i in range(3):
            data = {
                "titulo": f"Aviso {i}",
                "cuerpo": f"Cuerpo {i}.",
                "alcance": AlcanceAviso.GLOBAL.value,
                "inicio_en": utc_now() - timedelta(days=1),
                "fin_en": utc_now() + timedelta(days=1),
                "orden": i,
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        visibles = await repo.list_visibles(test_tenant.id)
        assert len(visibles) == 3
        assert visibles[0].orden == 0
        assert visibles[1].orden == 1
        assert visibles[2].orden == 2

    async def test_list_visibles_por_materia(self, repo, db_session, test_tenant, test_materia):
        materia_id = test_materia.id
        otra_materia_id = uuid.uuid4()

        data = {
            "titulo": "Por materia",
            "cuerpo": "Solo para MAT101.",
            "alcance": AlcanceAviso.POR_MATERIA.value,
            "materia_id": materia_id,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        visibles = await repo.list_visibles(
            test_tenant.id,
            materia_ids=[materia_id],
        )
        assert len(visibles) == 1

        visibles_otro = await repo.list_visibles(
            test_tenant.id,
            materia_ids=[otra_materia_id],
        )
        assert len(visibles_otro) == 0

    async def test_list_visibles_por_cohorte(self, repo, db_session, test_tenant, test_cohorte):
        cohorte_id = test_cohorte.id

        data = {
            "titulo": "Por cohorte",
            "cuerpo": "Solo para 2026.",
            "alcance": AlcanceAviso.POR_COHORTE.value,
            "cohorte_id": cohorte_id,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        visibles = await repo.list_visibles(
            test_tenant.id,
            cohorte_ids=[cohorte_id],
        )
        assert len(visibles) == 1

        visibles_otro = await repo.list_visibles(
            test_tenant.id,
            cohorte_ids=[uuid.uuid4()],
        )
        assert len(visibles_otro) == 0

    async def test_create_ack(self, repo, db_session, test_tenant, test_usuario):
        data = {
            "titulo": "Con ack",
            "cuerpo": "Requiere confirmación.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
            "requiere_ack": True,
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        usuario_id = test_usuario.id
        ack = await repo.create_ack(aviso.id, usuario_id, test_tenant.id)
        await db_session.commit()

        assert ack.id is not None
        assert ack.aviso_id == aviso.id
        assert ack.usuario_id == usuario_id
        assert ack.tenant_id == test_tenant.id
        assert ack.confirmado_at is not None

        fetched = await repo.get_ack(aviso.id, usuario_id, test_tenant.id)
        assert fetched is not None
        assert fetched.id == ack.id

    async def test_ack_unique(self, repo, db_session, test_tenant, test_usuario):
        data = {
            "titulo": "Ack único",
            "cuerpo": "Solo un ack por usuario.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        usuario_id = test_usuario.id
        await repo.create_ack(aviso.id, usuario_id, test_tenant.id)
        await db_session.commit()

        with pytest.raises(IntegrityError):
            await repo.create_ack(aviso.id, usuario_id, test_tenant.id)
            await db_session.commit()

    async def test_get_ack_count(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Contar acks",
            "cuerpo": "Varios usuarios ack.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        for _ in range(3):
            u = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"ack_{uuid.uuid4()}@t.com", dni="0", cuil="0")
            db_session.add(u)
            await db_session.flush()
            ack = await repo.create_ack(aviso.id, u.id, test_tenant.id)
            db_session.add(ack)
        await db_session.commit()

        count = await repo.get_ack_count(aviso.id, test_tenant.id)
        assert count == 3

    async def test_update_aviso(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Original",
            "cuerpo": "Cuerpo original.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now(),
            "fin_en": utc_now() + timedelta(days=30),
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        updated = await repo.update(aviso, {"titulo": "Modificado", "orden": 10})
        await db_session.commit()

        assert updated.titulo == "Modificado"
        assert updated.orden == 10
        assert updated.cuerpo == "Cuerpo original."

        fetched = await repo.get(aviso.id, test_tenant.id)
        assert fetched.titulo == "Modificado"
        assert fetched.orden == 10

    async def test_list_all_with_filters(self, repo, db_session, test_tenant):
        for i in range(3):
            data = {
                "titulo": f"Aviso {i}",
                "cuerpo": f"Cuerpo {i}.",
                "alcance": AlcanceAviso.GLOBAL.value if i % 2 == 0 else AlcanceAviso.POR_ROL.value,
                "rol_destino": "PROFESOR" if i % 2 == 1 else None,
                "severidad": SeveridadAviso.INFO.value,
                "inicio_en": utc_now() - timedelta(days=10),
                "fin_en": utc_now() + timedelta(days=10),
                "activo": True,
            }
            await repo.create(data, test_tenant.id)
        await db_session.commit()

        params = AvisoListParams(alcance=AlcanceAviso.POR_ROL.value)
        items, total = await repo.list_all(test_tenant.id, params)
        assert total == 1  # only one with PorRol
        assert items[0].titulo == "Aviso 1"

        params2 = AvisoListParams()
        items2, total2 = await repo.list_all(test_tenant.id, params2)
        assert total2 == 3

    async def test_delete_aviso(self, repo, db_session, test_tenant):
        data = {
            "titulo": "A eliminar",
            "cuerpo": "Será borrado.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now(),
            "fin_en": utc_now() + timedelta(days=7),
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        await repo.delete(aviso.id, test_tenant.id)
        await db_session.commit()

        fetched = await repo.get(aviso.id, test_tenant.id)
        assert fetched is None

    async def test_list_acks_for_aviso(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Ack list",
            "cuerpo": "Listar acknowledgments.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        aviso = await repo.create(data, test_tenant.id)
        await db_session.commit()

        usuario_ids = []
        for _ in range(3):
            u = Usuario(id=uuid.uuid4(), tenant_id=test_tenant.id, email=f"listack_{uuid.uuid4()}@t.com", dni="0", cuil="0")
            db_session.add(u)
            await db_session.flush()
            usuario_ids.append(u.id)
            ack = await repo.create_ack(aviso.id, u.id, test_tenant.id)
            db_session.add(ack)
        await db_session.commit()

        items, total = await repo.list_acks_for_aviso(aviso.id, test_tenant.id)
        assert total == 3
        assert len(items) == 3
        returned_ids = {a.usuario_id for a in items}
        assert returned_ids == set(usuario_ids)

    async def test_count_visibles(self, repo, db_session, test_tenant):
        data = {
            "titulo": "Contar visibles",
            "cuerpo": "Test count.",
            "alcance": AlcanceAviso.GLOBAL.value,
            "inicio_en": utc_now() - timedelta(days=1),
            "fin_en": utc_now() + timedelta(days=1),
        }
        await repo.create(data, test_tenant.id)
        await db_session.commit()

        count = await repo.count_visibles(test_tenant.id)
        assert count == 1
