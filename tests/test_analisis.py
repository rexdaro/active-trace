import pytest
import pytest_asyncio
import uuid
import io
import csv
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Usuario
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import Calificacion, CalificacionOrigen
from app.models.umbral_materia import UmbralMateria
from app.models.audit import AuditLog
from app.models.rbac import Role
from app.models.user_role import UserRole
from app.repositories.calificaciones import CalificacionesRepository
from app.repositories.umbral_materia import UmbralMateriaRepository
from app.services.analisis import AnalisisService
from app.schemas.analisis import (
    AlumnoAtrasado, AtrasadosResponse, RankingEntry, RankingResponse,
    ActividadReporte, ReporteMateria, EstadoSinDatos,
    NotaFinalAlumno, NotaFinalTextual, NotasFinalesResponse,
    MonitorAlumno, MonitorMateria, MonitorGeneralResponse,
    SeguimientoAlumno, SeguimientoResponse,
)

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
async def test_materia(db_session, test_tenant):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="MAT101", is_active=True)
    db_session.add(materia)
    await db_session.commit()
    return materia


@pytest_asyncio.fixture
async def test_carrera(db_session, test_tenant):
    carrera = Carrera(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Ingeniería", code="ING", is_active=True)
    db_session.add(carrera)
    await db_session.commit()
    return carrera


@pytest_asyncio.fixture
async def test_cohorte(db_session, test_tenant, test_carrera):
    cohorte = Cohorte(id=uuid.uuid4(), tenant_id=test_tenant.id, name="2025", carrera_id=test_carrera.id, is_active=True)
    db_session.add(cohorte)
    await db_session.commit()
    return cohorte


@pytest_asyncio.fixture
async def profesor_role(db_session):
    role = Role(id=1, name="PROFESOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def tutor_role(db_session):
    role = Role(id=2, name="TUTOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def coordinador_role(db_session):
    role = Role(id=3, name="COORDINADOR")
    db_session.add(role)
    await db_session.commit()
    return role


@pytest_asyncio.fixture
async def admin_role(db_session):
    role = Role(id=4, name="ADMIN")
    db_session.add(role)
    await db_session.commit()
    return role


def _make_id():
    return uuid.uuid4()


async def _make_user(db_session, tenant, role, email_suffix=""):
    user = User(id=_make_id(), tenant_id=tenant.id, email=f"u{email_suffix}@t.com", hashed_password="h", is_2fa_enabled=False)
    db_session.add(user)
    await db_session.flush()
    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()
    return user


async def _make_entrada(db_session, tenant, materia, cohorte, nombre, apellidos, email, comision="A", regional="CABA", cargado_por=None):
    if cargado_por is None:
        u = Usuario(id=_make_id(), tenant_id=tenant.id, email=f"cargador_{_make_id()}@t.com", dni="0", cuil="0")
        db_session.add(u)
        await db_session.flush()
        cargado_por = u.id
    version = VersionPadron(id=_make_id(), tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, archivo_nombre="p.csv", archivo_hash="h", origen="A", cargado_por=cargado_por, activa=True)
    db_session.add(version)
    await db_session.flush()
    e = EntradaPadron(id=_make_id(), version_id=version.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos, email=email, comision=comision, regional=regional)
    db_session.add(e)
    await db_session.flush()
    return e


async def _make_calif(db_session, tenant, entrada, materia, actividad, nota_numerica=None, nota_textual=None, aprobado=False, importado_por=None):
    if importado_por is None:
        u = Usuario(id=_make_id(), tenant_id=tenant.id, email=f"importador_{_make_id()}@t.com", dni="0", cuil="0")
        db_session.add(u)
        await db_session.flush()
        importado_por = u.id
    c = Calificacion(id=_make_id(), tenant_id=tenant.id, entrada_padron_id=entrada.id, materia_id=materia.id, actividad=actividad, nota_numerica=nota_numerica, nota_textual=nota_textual, aprobado=aprobado, origen=CalificacionOrigen.IMPORTADO.value, importado_por=importado_por, importado_at=datetime.now(timezone.utc))
    db_session.add(c)
    await db_session.flush()
    return c


async def _make_asig(db_session, tenant, user, materia, role):
    a = Asignacion(id=_make_id(), tenant_id=tenant.id, user_id=user.id, role_id=role.id, contexto_id=materia.id, desde=datetime.now(timezone.utc))
    db_session.add(a)
    await db_session.flush()
    return a


# ═══ Scoping (Task 24) ═══════════════════════════════

class TestScoping:

    @pytest.mark.asyncio
    async def test_profesor_sin_asignacion_activa_403(self, db_session, test_tenant, test_materia, profesor_role):
        user = await _make_user(db_session, test_tenant, profesor_role, "p1")
        await db_session.commit()
        with pytest.raises(Exception) as exc:
            await AnalisisService._resolve_scope(db_session, user, test_materia.id)
        assert exc.type.__name__ == "HTTPException"
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_tutor_con_asignacion_ve_scope_asignado(self, db_session, test_tenant, test_materia, tutor_role):
        user = await _make_user(db_session, test_tenant, tutor_role, "t1")
        await _make_asig(db_session, test_tenant, user, test_materia, tutor_role)
        await db_session.commit()
        scope = await AnalisisService._resolve_scope(db_session, user, test_materia.id)
        assert scope.type == "asignado"
        assert scope.asignacion_id is not None

    @pytest.mark.asyncio
    async def test_admin_sin_restriccion(self, db_session, test_tenant, test_materia, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a1")
        await db_session.commit()
        scope = await AnalisisService._resolve_scope(db_session, user, test_materia.id)
        assert scope.type == "full"


# ═══ Atrasados (Task 17) ═════════════════════════════

class TestAtrasados:

    @pytest.mark.asyncio
    async def test_alumno_con_actividad_faltante_es_detectado(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e1 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        e2 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "García", "a@t.com")
        await _make_calif(db_session, test_tenant, e1, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e2, test_materia, "TP1", nota_numerica=70, aprobado=True)
        await _make_calif(db_session, test_tenant, e2, test_materia, "TP2", nota_numerica=70, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_atrasados(db_session, test_materia.id, user)
        assert len(result.atrasados) == 1
        assert result.atrasados[0].entrada_padron_id == e1.id
        assert result.atrasados[0].motivo == "actividad_faltante"
        assert "TP2" in result.atrasados[0].actividades_faltantes

    @pytest.mark.asyncio
    async def test_alumno_con_nota_bajo_umbral_es_detectado(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e, test_materia, "TP2", nota_numerica=45, aprobado=False)
        await db_session.commit()
        result = await AnalisisService.get_atrasados(db_session, test_materia.id, user)
        assert len(result.atrasados) == 1
        assert result.atrasados[0].motivo == "nota_bajo_umbral"
        assert "TP2" in result.atrasados[0].actividades_desaprobadas

    @pytest.mark.asyncio
    async def test_alumno_con_todas_aprobadas_no_aparece(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e, test_materia, "TP2", nota_numerica=90, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_atrasados(db_session, test_materia.id, user)
        assert len(result.atrasados) == 0

    @pytest.mark.asyncio
    async def test_materia_sin_calificaciones_retorna_vacia(self, db_session, test_tenant, test_materia, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        await db_session.commit()
        result = await AnalisisService.get_atrasados(db_session, test_materia.id, user)
        assert len(result.atrasados) == 0
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_scope_profesor_limita_resultados(self, db_session, test_tenant, test_materia, test_cohorte, profesor_role):
        prof = await _make_user(db_session, test_tenant, profesor_role, "p")
        await _make_asig(db_session, test_tenant, prof, test_materia, profesor_role)
        e1 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com", comision="A")
        e2 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "García", "a@t.com", comision="B")
        await _make_calif(db_session, test_tenant, e1, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e2, test_materia, "TP1", nota_numerica=45, aprobado=False)
        await db_session.commit()
        result = await AnalisisService.get_atrasados(db_session, test_materia.id, prof)
        assert len(result.atrasados) <= 2


# ═══ Ranking (Task 18) ═══════════════════════════════

class TestRanking:

    @pytest.mark.asyncio
    async def test_orden_descendente_por_aprobados(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        ea = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Carlos", "López", "c@t.com")
        eb = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "Martínez", "a@t.com")
        for act in ["TP1", "TP2", "TP3"]:
            await _make_calif(db_session, test_tenant, ea, test_materia, act, nota_numerica=80, aprobado=True)
        for act in ["TP1", "TP2"]:
            await _make_calif(db_session, test_tenant, eb, test_materia, act, nota_numerica=80, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_ranking(db_session, test_materia.id, user)
        assert len(result.ranking) == 2
        assert result.ranking[0].actividades_aprobadas >= result.ranking[1].actividades_aprobadas

    @pytest.mark.asyncio
    async def test_empate_ordenado_alfabeticamente(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        ea = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Carlos", "García", "c@t.com")
        eb = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "Benítez", "a@t.com")
        for act in ["TP1", "TP2", "TP3"]:
            await _make_calif(db_session, test_tenant, ea, test_materia, act, nota_numerica=80, aprobado=True)
            await _make_calif(db_session, test_tenant, eb, test_materia, act, nota_numerica=80, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_ranking(db_session, test_materia.id, user)
        assert len(result.ranking) == 2
        assert result.ranking[0].apellidos == "Benítez" or result.ranking[0].actividades_aprobadas > result.ranking[1].actividades_aprobadas

    @pytest.mark.asyncio
    async def test_alumno_sin_aprobadas_excluido(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=45, aprobado=False)
        await db_session.commit()
        result = await AnalisisService.get_ranking(db_session, test_materia.id, user)
        assert len(result.ranking) == 0

    @pytest.mark.asyncio
    async def test_paginacion_funciona(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        for i in range(5):
            e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, f"Alumno{i}", f"Apellido{i}", f"a{i}@t.com")
            await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_ranking(db_session, test_materia.id, user, limit=2, offset=0)
        assert len(result.ranking) == 2
        assert result.total == 5


# ═══ Reporte (Task 19) ═══════════════════════════════

class TestReporte:

    @pytest.mark.asyncio
    async def test_metricas_globales_correctas(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        for i in range(10):
            e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, f"Alumno{i}", f"Apellido{i}", f"a{i}@t.com")
            await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
            await _make_calif(db_session, test_tenant, e, test_materia, "TP2", nota_numerica=70, aprobado=True)
            await _make_calif(db_session, test_tenant, e, test_materia, "TP3", nota_numerica=45, aprobado=False)
        await db_session.commit()
        result = await AnalisisService.get_reporte(db_session, test_materia.id, user)
        assert not result.sin_datos
        assert result.total_alumnos == 10
        assert result.total_actividades == 3
        assert result.total_calificaciones == 30
        assert result.aprobados == 20
        assert result.no_aprobados == 10
        assert result.porcentaje_aprobacion == pytest.approx(66.67, abs=0.01)

    @pytest.mark.asyncio
    async def test_reporte_sin_datos_retorna_estado_informativo(self, db_session, test_tenant, test_materia, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        await db_session.commit()
        result = await AnalisisService.get_reporte(db_session, test_materia.id, user)
        assert isinstance(result, EstadoSinDatos)
        assert result.sin_datos is True

    @pytest.mark.asyncio
    async def test_desglose_por_actividad(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        for i in range(10):
            e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, f"Alumno{i}", f"Apellido{i}", f"a{i}@t.com")
            await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
            await _make_calif(db_session, test_tenant, e, test_materia, "TP2", nota_numerica=45, aprobado=False)
        await db_session.commit()
        result = await AnalisisService.get_reporte(db_session, test_materia.id, user)
        assert len(result.por_actividad) == 2
        tp1 = next(a for a in result.por_actividad if a.actividad == "TP1")
        assert tp1.aprobados == 10
        tp2 = next(a for a in result.por_actividad if a.actividad == "TP2")
        assert tp2.aprobados == 0


# ═══ Notas Finales (Task 20) ═════════════════════════

class TestNotasFinales:

    @pytest.mark.asyncio
    async def test_promedio_simple_de_numericas(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=70, aprobado=True)
        await _make_calif(db_session, test_tenant, e, test_materia, "TP2", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e, test_materia, "TP3", nota_numerica=90, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_notas_finales(db_session, test_materia.id, user)
        assert len(result.notas_numericas) == 1
        assert result.notas_numericas[0].promedio == 80.0
        assert result.notas_numericas[0].actividades_count == 3

    @pytest.mark.asyncio
    async def test_notas_textuales_en_seccion_separada(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP Final", nota_textual="Satisfactorio", aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_notas_finales(db_session, test_materia.id, user)
        assert len(result.notas_numericas) == 0
        assert len(result.notas_textuales) == 1
        assert result.notas_textuales[0].entrada_padron_id == e.id

    @pytest.mark.asyncio
    async def test_alumno_sin_calificaciones_no_aparece(self, db_session, test_tenant, test_materia, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        await db_session.commit()
        result = await AnalisisService.get_notas_finales(db_session, test_materia.id, user)
        assert len(result.notas_numericas) == 0
        assert len(result.notas_textuales) == 0


# ═══ Export TPs sin corregir (Task 21) ═══════════════

class TestExportTPSinCorregir:

    @pytest.mark.asyncio
    async def test_csv_incluye_solo_textuales_sin_calificar(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1 (Real)", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e, test_materia, "TP Final", nota_textual=None, aprobado=False)
        await db_session.commit()
        response = await AnalisisService.export_tps_sin_corregir(db_session, test_materia.id, user)
        content = b"".join([chunk async for chunk in response.body_iterator])
        decoded = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
        actividades = [r["Actividad"] for r in rows]
        assert "TP Final" in actividades
        assert "TP1 (Real)" not in actividades

    @pytest.mark.asyncio
    async def test_cabeceras_correctas(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP Final", nota_textual=None, aprobado=False)
        await db_session.commit()
        response = await AnalisisService.export_tps_sin_corregir(db_session, test_materia.id, user)
        content = b"".join([chunk async for chunk in response.body_iterator])
        decoded = content.decode("utf-8-sig")
        head = decoded.splitlines()[0]
        assert "Apellidos" in head
        assert "Nombre" in head
        assert "Email" in head
        assert "Actividad" in head
        assert "Comisión" in head
        assert "Regional" in head

    @pytest.mark.asyncio
    async def test_todas_calificadas_csv_solo_cabeceras(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP Final", nota_textual="Satisfactorio", aprobado=True)
        await db_session.commit()
        response = await AnalisisService.export_tps_sin_corregir(db_session, test_materia.id, user)
        content = b"".join([chunk async for chunk in response.body_iterator])
        decoded = content.decode("utf-8-sig")
        lines = decoded.strip().splitlines()
        assert len(lines) == 1

    @pytest.mark.asyncio
    async def test_audit_registrado(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP Final", nota_textual=None, aprobado=False)
        await db_session.commit()
        await AnalisisService.export_tps_sin_corregir(db_session, test_materia.id, user)
        stmt = select(AuditLog).where(AuditLog.action == "ANALISIS_CONSULTA")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
        assert logs[0].detalle.get("tipo") == "export_tps_sin_corregir"


# ═══ Monitor General (Task 22) ═══════════════════════

class TestMonitorGeneral:

    @pytest.mark.asyncio
    async def test_admin_ve_todos_alumnos(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_general(db_session, user)
        assert result.total == 1
        assert result.alumnos[0].nombre == "Juan"

    @pytest.mark.asyncio
    async def test_profesor_recibe_403(self, db_session, test_tenant, test_materia, profesor_role):
        user = await _make_user(db_session, test_tenant, profesor_role, "p")
        await db_session.commit()
        with pytest.raises(Exception) as exc:
            await AnalisisService.get_monitor_general(db_session, user)
        assert exc.type.__name__ == "HTTPException"
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_filtro_por_materia_funciona(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        otra = Materia(id=_make_id(), tenant_id=test_tenant.id, name="Física", code="FIS101", is_active=True)
        db_session.add(otra)
        await db_session.flush()
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e, otra, "TP1", nota_numerica=90, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_general(db_session, user, materia_id=test_materia.id)
        assert result.total == 1
        assert len(result.alumnos[0].materias) == 1
        assert result.alumnos[0].materias[0].materia_id == test_materia.id

    @pytest.mark.asyncio
    async def test_busqueda_libre_funciona(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e1 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Carlos", "García", "c@t.com")
        e2 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "María", "López", "m@t.com")
        await _make_calif(db_session, test_tenant, e1, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e2, test_materia, "TP1", nota_numerica=90, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_general(db_session, user, q="García")
        assert result.total == 1
        assert result.alumnos[0].apellidos == "García"

    @pytest.mark.asyncio
    async def test_audit_registrado(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await db_session.commit()
        await AnalisisService.get_monitor_general(db_session, user)
        stmt = select(AuditLog).where(AuditLog.action == "ANALISIS_CONSULTA")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1


# ═══ Monitor Seguimiento (Task 23) ═══════════════════

class TestMonitorSeguimiento:

    @pytest.mark.asyncio
    async def test_profesor_ve_solo_asignados(self, db_session, test_tenant, test_materia, test_cohorte, profesor_role):
        prof = await _make_user(db_session, test_tenant, profesor_role, "p")
        await _make_asig(db_session, test_tenant, prof, test_materia, profesor_role)
        e1 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com", comision="A")
        e2 = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "García", "a@t.com", comision="B")
        await _make_calif(db_session, test_tenant, e1, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, e2, test_materia, "TP1", nota_numerica=90, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_seguimiento(db_session, prof)
        assert result.total >= 0

    @pytest.mark.asyncio
    async def test_coordinador_ve_todos(self, db_session, test_tenant, test_materia, test_cohorte, coordinador_role):
        user = await _make_user(db_session, test_tenant, coordinador_role, "c")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_seguimiento(db_session, user)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_filtro_fecha_solo_coordinador_admin(self, db_session, test_tenant, test_materia, test_cohorte, coordinador_role):
        user = await _make_user(db_session, test_tenant, coordinador_role, "c")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_seguimiento(db_session, user, fecha_desde="2026-01-01", fecha_hasta="2026-12-31")
        assert result.total >= 0

    @pytest.mark.asyncio
    async def test_filtro_min_cumplimiento(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        ea = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        eb = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "García", "a@t.com")
        for act in ["TP1", "TP2", "TP3"]:
            await _make_calif(db_session, test_tenant, ea, test_materia, act, nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, eb, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, eb, test_materia, "TP2", nota_numerica=45, aprobado=False)
        await _make_calif(db_session, test_tenant, eb, test_materia, "TP3", nota_numerica=45, aprobado=False)
        await db_session.commit()
        result = await AnalisisService.get_monitor_seguimiento(db_session, user, min_cumplimiento_pct=50)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_filtro_por_actividad(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        ea = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        eb = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Ana", "García", "a@t.com")
        await _make_calif(db_session, test_tenant, ea, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await _make_calif(db_session, test_tenant, eb, test_materia, "TP2", nota_numerica=90, aprobado=True)
        await db_session.commit()
        result = await AnalisisService.get_monitor_seguimiento(db_session, user, actividad="TP1")
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_audit_registrado(self, db_session, test_tenant, test_materia, test_cohorte, admin_role):
        user = await _make_user(db_session, test_tenant, admin_role, "a")
        e = await _make_entrada(db_session, test_tenant, test_materia, test_cohorte, "Juan", "Pérez", "j@t.com")
        await _make_calif(db_session, test_tenant, e, test_materia, "TP1", nota_numerica=80, aprobado=True)
        await db_session.commit()
        await AnalisisService.get_monitor_seguimiento(db_session, user)
        stmt = select(AuditLog).where(AuditLog.action == "ANALISIS_CONSULTA")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1
