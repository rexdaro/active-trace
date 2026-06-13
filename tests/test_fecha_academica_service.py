import pytest
import pytest_asyncio
import uuid
import os
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.services.fechas_academicas import FechaAcademicaService
from app.schemas.fecha_academica import FechaAcademicaCreate, FechaAcademicaUpdate, FechaAcademicaListParams

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


class TestFechaAcademicaService:

    @pytest.mark.asyncio
    async def test_create_success(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        request = FechaAcademicaCreate(
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="1er Parcial",
        )
        result = await FechaAcademicaService.create(db_session, request, admin_user)

        assert result.id is not None
        assert result.titulo == "1er Parcial"
        assert result.tipo == TipoFecha.PARCIAL.value
        assert result.tenant_id == test_tenant.id
        assert result.materia_id == test_materia.id
        assert result.cohorte_id == test_cohorte.id
        assert result.numero == 1

    @pytest.mark.asyncio
    async def test_create_invalid_materia_404(self, db_session, test_tenant, admin_user, test_cohorte):
        from fastapi import HTTPException
        request = FechaAcademicaCreate(
            materia_id=uuid.uuid4(),
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Sin materia",
        )
        with pytest.raises(HTTPException) as exc:
            await FechaAcademicaService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_cohorte_404(self, db_session, test_tenant, admin_user, test_materia):
        from fastapi import HTTPException
        request = FechaAcademicaCreate(
            materia_id=test_materia.id,
            cohorte_id=uuid.uuid4(),
            tipo=TipoFecha.PARCIAL,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Sin cohorte",
        )
        with pytest.raises(HTTPException) as exc:
            await FechaAcademicaService.create(db_session, request, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_success(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Test get",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        result = await FechaAcademicaService.get(db_session, fecha_obj.id, admin_user)
        assert result is not None
        assert result.id == fecha_obj.id
        assert result.titulo == "Test get"

    @pytest.mark.asyncio
    async def test_get_not_found_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await FechaAcademicaService.get(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_success(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="Original",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        request = FechaAcademicaUpdate(titulo="Modificado", numero=2)
        result = await FechaAcademicaService.update(db_session, fecha_obj.id, request, admin_user)

        assert result.titulo == "Modificado"
        assert result.numero == 2

    @pytest.mark.asyncio
    async def test_delete_soft(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="A eliminar",
        )
        db_session.add(fecha_obj)
        await db_session.commit()

        await FechaAcademicaService.delete(db_session, fecha_obj.id, admin_user)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await FechaAcademicaService.get(db_session, fecha_obj.id, admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await FechaAcademicaService.delete(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_with_filters(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        for i in range(3):
            fecha_obj = FechaAcademica(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                materia_id=test_materia.id,
                cohorte_id=test_cohorte.id,
                tipo=TipoFecha.PARCIAL.value,
                numero=i + 1,
                periodo="2026",
                fecha=date(2026, 6, 15),
                titulo=f"Parcial {i + 1}",
            )
            db_session.add(fecha_obj)
        await db_session.commit()

        params = FechaAcademicaListParams()
        items, total = await FechaAcademicaService.list(db_session, admin_user, params)
        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_generate_html_returns_table(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        fecha_obj = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="1er Parcial",
        )
        db_session.add(fecha_obj)

        fecha_obj2 = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.TP.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 10),
            titulo="TP 1",
        )
        db_session.add(fecha_obj2)
        await db_session.commit()

        html = await FechaAcademicaService.generate_html(db_session, fecha_obj.id, admin_user)
        assert "<table>" in html
        assert "</table>" in html
        assert "1er Parcial" in html
        assert "TP 1" in html

    @pytest.mark.asyncio
    async def test_generate_html_ordered_by_fecha(self, db_session, test_tenant, admin_user, test_materia, test_cohorte):
        f1 = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=2,
            periodo="2026",
            fecha=date(2026, 7, 15),
            titulo="2do Parcial",
        )
        db_session.add(f1)
        f2 = FechaAcademica(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            materia_id=test_materia.id,
            cohorte_id=test_cohorte.id,
            tipo=TipoFecha.PARCIAL.value,
            numero=1,
            periodo="2026",
            fecha=date(2026, 6, 15),
            titulo="1er Parcial",
        )
        db_session.add(f2)
        await db_session.commit()

        html = await FechaAcademicaService.generate_html(db_session, f1.id, admin_user)
        tr_pos_1er = html.index("1er Parcial")
        tr_pos_2do = html.index("2do Parcial")
        assert tr_pos_1er < tr_pos_2do

    @pytest.mark.asyncio
    async def test_generate_html_nonexistent_fecha_404(self, db_session, test_tenant, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await FechaAcademicaService.generate_html(db_session, uuid.uuid4(), admin_user)
        assert exc.value.status_code == 404
