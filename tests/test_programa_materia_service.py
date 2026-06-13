import pytest
import pytest_asyncio
import uuid
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.programa_materia import ProgramaMateria
from app.services.programas_materia import ProgramaMateriaService
from app.schemas.programa_materia import ProgramaMateriaCreate, ProgramaMateriaUpdate, ProgramaMateriaListParams

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
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="admin@test.com",
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


class TestProgramaMateriaService:

    @pytest.mark.asyncio
    async def test_create_success(self, db_session, test_tenant, admin_user, test_materia, test_carrera, test_cohorte):
        request = ProgramaMateriaCreate(
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Programa 2026",
        )
        result = await ProgramaMateriaService.create(db_session, request, admin_user)

        assert result.id is not None
        assert result.titulo == "Programa 2026"
        assert result.tenant_id == test_tenant.id
        assert result.materia_id == test_materia.id
        assert result.carrera_id == test_carrera.id
        assert result.cohorte_id == test_cohorte.id

    @pytest.mark.asyncio
    async def test_create_invalid_materia_404(self, db_session, test_tenant, admin_user, test_carrera, test_cohorte):
        from fastapi import HTTPException
        request = ProgramaMateriaCreate(
            materia_id=uuid.uuid4(),
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Sin materia",
        )
        with pytest.raises(HTTPException) as exc:
            await ProgramaMateriaService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_carrera_404(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        from fastapi import HTTPException
        request = ProgramaMateriaCreate(
            materia_id=test_materia.id,
            carrera_id=uuid.uuid4(),
            cohorte_id=test_cohorte.id,
            titulo="Sin carrera",
        )
        with pytest.raises(HTTPException) as exc:
            await ProgramaMateriaService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_cohorte_404(self, db_session, test_tenant, admin_user, test_materia, test_carrera):
        from fastapi import HTTPException
        request = ProgramaMateriaCreate(
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=uuid.uuid4(),
            titulo="Sin cohorte",
        )
        with pytest.raises(HTTPException) as exc:
            await ProgramaMateriaService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_success(self, db_session, test_tenant, admin_user, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Test get",
        )
        db_session.add(programa)
        await db_session.commit()

        result = await ProgramaMateriaService.get(db_session, programa.id, admin_user)
        assert result is not None
        assert result.id == programa.id
        assert result.titulo == "Test get"

    @pytest.mark.asyncio
    async def test_get_not_found_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await ProgramaMateriaService.get(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_success(self, db_session, test_tenant, admin_user, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="Original",
        )
        db_session.add(programa)
        await db_session.commit()

        request = ProgramaMateriaUpdate(titulo="Modificado", referencia_archivo="v2.pdf")
        result = await ProgramaMateriaService.update(db_session, programa.id, request, admin_user)

        assert result.titulo == "Modificado"
        assert result.referencia_archivo == "v2.pdf"

    @pytest.mark.asyncio
    async def test_delete_soft(self, db_session, test_tenant, admin_user, test_materia, test_carrera, test_cohorte):
        programa = ProgramaMateria(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            carrera_id=test_carrera.id,
            cohorte_id=test_cohorte.id,
            titulo="A eliminar",
        )
        db_session.add(programa)
        await db_session.commit()

        await ProgramaMateriaService.delete(db_session, programa.id, admin_user)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await ProgramaMateriaService.get(db_session, programa.id, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await ProgramaMateriaService.delete(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_with_filters(self, db_session, test_tenant, admin_user, test_materia, test_carrera, test_cohorte):
        for i in range(3):
            programa = ProgramaMateria(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                materia_id=test_materia.id,
                carrera_id=test_carrera.id,
                cohorte_id=test_cohorte.id,
                titulo=f"Programa {i}",
            )
            db_session.add(programa)
        await db_session.commit()

        params = ProgramaMateriaListParams()
        items, total = await ProgramaMateriaService.list(db_session, admin_user, params)
        assert total == 3
        assert len(items) == 3
