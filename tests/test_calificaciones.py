import pytest
import pytest_asyncio
import uuid
import io
import os
import time
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import Usuario, User
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import Calificacion, CalificacionOrigen
from app.models.umbral_materia import UmbralMateria
from app.models.audit import AuditLog
from app.repositories.calificaciones import CalificacionesRepository
from app.repositories.umbral_materia import UmbralMateriaRepository
from app.services.calificaciones import CalificacionesService, _preview_store, DEFAULT_UMBRAL_PCT, DEFAULT_VALORES_APROBATORIOS
from app.schemas.calificacion import (
    CalificacionPreviewResponse,
    CalificacionConfirmResponse,
    CalificacionListResponse,
    FinalizacionPreviewResponse,
    FinalizacionConfirmResponse,
    UmbralRead,
    UmbralUpdateRequest,
    VaciarResponse,
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
async def mock_user(db_session, test_tenant):
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="teacher@test.com",
        hashed_password="hashed",
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_materia(db_session, test_tenant):
    materia = Materia(id=uuid.uuid4(), tenant_id=test_tenant.id, name="Matemática", code="MAT101", is_active=True)
    db_session.add(materia)
    await db_session.commit()
    return materia


@pytest_asyncio.fixture
async def test_cohorte(db_session, test_tenant):
    cohorte = Cohorte(id=uuid.uuid4(), tenant_id=test_tenant.id, name="2025", carrera_id=uuid.uuid4(), is_active=True)
    db_session.add(cohorte)
    await db_session.commit()
    return cohorte


@pytest_asyncio.fixture
async def test_entrada_padron(db_session, test_tenant, test_materia, test_cohorte, mock_user):
    from app.models.padron import VersionPadron, EntradaPadron
    version = VersionPadron(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        materia_id=test_materia.id,
        cohorte_id=test_cohorte.id,
        archivo_nombre="padron.csv",
        archivo_hash="abc123",
        origen="Archivo",
        cargado_por=mock_user.id,
        activa=True,
    )
    db_session.add(version)
    await db_session.commit()

    entrada = EntradaPadron(
        id=uuid.uuid4(),
        version_id=version.id,
        tenant_id=test_tenant.id,
        usuario_id=None,
        nombre="Juan",
        apellidos="Pérez",
        email="juan@test.com",
        comision="A",
        regional="CABA",
    )
    db_session.add(entrada)
    await db_session.commit()
    return entrada


@pytest_asyncio.fixture
async def test_asignacion(db_session, test_tenant, test_materia, mock_user):
    from app.models.rbac import Role
    role = Role(name="PROFESOR")
    db_session.add(role)
    await db_session.commit()

    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=mock_user.id,
        role_id=role.id,
        contexto_id=test_materia.id,
        desde=datetime.now(timezone.utc),
    )
    db_session.add(asignacion)
    await db_session.commit()
    return asignacion


# ═══════════════════════════════════════════════════════════════════════════════
# Task 18: Tests de derivación de aprobado
# ═══════════════════════════════════════════════════════════════════════════════

class TestDerivacionAprobado:

    @pytest.mark.asyncio
    async def test_numerica_sobre_umbral_aprueba(self, db_session, test_tenant, test_materia, test_asignacion):
        aprobado = await CalificacionesService.derivar_aprobado(
            db_session, 75, None, test_materia.id, test_asignacion.id, test_tenant.id,
        )
        assert aprobado is True

    @pytest.mark.asyncio
    async def test_numerica_bajo_umbral_no_aprueba(self, db_session, test_tenant, test_materia, test_asignacion):
        aprobado = await CalificacionesService.derivar_aprobado(
            db_session, 45, None, test_materia.id, test_asignacion.id, test_tenant.id,
        )
        assert aprobado is False

    @pytest.mark.asyncio
    async def test_textual_aprobatorio_aprueba(self, db_session, test_tenant, test_materia, test_asignacion):
        aprobado = await CalificacionesService.derivar_aprobado(
            db_session, None, "Supera lo esperado", test_materia.id, test_asignacion.id, test_tenant.id,
        )
        assert aprobado is True

    @pytest.mark.asyncio
    async def test_textual_no_aprobatorio_no_aprueba(self, db_session, test_tenant, test_materia, test_asignacion):
        aprobado = await CalificacionesService.derivar_aprobado(
            db_session, None, "No satisfactorio", test_materia.id, test_asignacion.id, test_tenant.id,
        )
        assert aprobado is False

    @pytest.mark.asyncio
    async def test_umbral_defecto_60_sin_configuracion(self, db_session, test_tenant, test_materia):
        aprobado = await CalificacionesService.derivar_aprobado(
            db_session, 60, None, test_materia.id, None, test_tenant.id,
        )
        assert aprobado is True

    @pytest.mark.asyncio
    async def test_umbral_personalizado_se_usa(self, db_session, test_tenant, test_materia, test_asignacion):
        repo = UmbralMateriaRepository(db_session)
        await repo.upsert(
            asignacion_id=test_asignacion.id,
            materia_id=test_materia.id,
            tenant_id=test_tenant.id,
            umbral_pct=80,
            valores_aprobatorios=["Satisfactorio", "Excelente"],
        )
        aprobado = await CalificacionesService.derivar_aprobado(
            db_session, 75, None, test_materia.id, test_asignacion.id, test_tenant.id,
        )
        assert aprobado is False


# ═══════════════════════════════════════════════════════════════════════════════
# Task 19: Tests de import de calificaciones
# ═══════════════════════════════════════════════════════════════════════════════

class TestImportCalificaciones:

    def _make_xlsx(self, headers: list, rows: list[list]) -> bytes:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue()

    def _make_csv(self, headers: list, rows: list[list], delimiter=",") -> bytes:
        lines = [delimiter.join(headers)]
        for row in rows:
            lines.append(delimiter.join(str(c) for c in row))
        return "\n".join(lines).encode("utf-8")

    def _fake_upload(self, filename: str, content: bytes):
        class FakeUploadFile:
            pass
        f = FakeUploadFile()
        f.filename = filename
        f._content = content
        f._read = False
        async def read():
            return f._content
        f.read = read
        return f

    @pytest.mark.asyncio
    async def test_preview_xlsx_detecta_columnas(self, db_session, test_tenant, test_materia, test_entrada_padron):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP1 (Real)", "TP2 (Real)", "TP Final"],
            [
                ["Juan", "Pérez", "juan@test.com", 75, 80, "Satisfactorio"],
            ],
        )
        file = self._fake_upload("califs.xlsx", content)
        result = await CalificacionesService.preview(test_materia.id, file)

        assert "preview_token" in result
        assert result["alumnos_count"] == 1
        actividades = result["actividades_detectadas"]
        nombres = {a["nombre"] for a in actividades}
        assert "TP1" in nombres
        assert "TP2" in nombres
        assert "TP Final" in nombres
        tipos = {a["nombre"]: a["tipo"] for a in actividades}
        assert tipos["TP1"] == "numerica"
        assert tipos["TP Final"] == "textual"

    @pytest.mark.asyncio
    async def test_preview_csv_funciona(self, db_session, test_tenant, test_materia, test_entrada_padron):
        content = self._make_csv(
            ["Nombre", "Apellido", "Email", "TP1 (Real)", "TP Final"],
            [
                ["Juan", "Pérez", "juan@test.com", "75", "Satisfactorio"],
            ],
        )
        file = self._fake_upload("califs.csv", content)
        result = await CalificacionesService.preview(test_materia.id, file)

        assert result["alumnos_count"] == 1
        actividades = result["actividades_detectadas"]
        assert len(actividades) == 2

    @pytest.mark.asyncio
    async def test_confirm_crea_solo_seleccionadas(self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP1 (Real)", "TP Final"],
            [
                ["Juan", "Pérez", "juan@test.com", 75, "Satisfactorio"],
            ],
        )
        file = self._fake_upload("califs.xlsx", content)
        preview = await CalificacionesService.preview(test_materia.id, file)
        token = preview["preview_token"]

        result = await CalificacionesService.confirm(db_session, token, mock_user, ["TP1"])
        assert result["calificaciones_count"] == 1

        repo = CalificacionesRepository(db_session)
        califs, total = await repo.get_by_materia(test_materia.id, test_tenant.id)
        assert total == 1
        assert califs[0].actividad == "TP1"

    @pytest.mark.asyncio
    async def test_confirm_deriva_aprobado(self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user, test_asignacion):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP1 (Real)", "TP Final"],
            [
                ["Juan", "Pérez", "juan@test.com", 75, "Satisfactorio"],
            ],
        )
        file = self._fake_upload("califs.xlsx", content)
        preview = await CalificacionesService.preview(test_materia.id, file)
        token = preview["preview_token"]

        result = await CalificacionesService.confirm(db_session, token, mock_user, ["TP1", "TP Final"])
        assert result["calificaciones_count"] == 2
        assert result["aprobados_count"] == 2
        assert result["no_aprobados_count"] == 0

    @pytest.mark.asyncio
    async def test_archivo_invalido_400(self, db_session, test_tenant, test_materia):
        file = self._fake_upload("califs.pdf", b"fake pdf content")
        with pytest.raises(Exception) as exc:
            await CalificacionesService.preview(test_materia.id, file)
        assert exc.type.__name__ in ("HTTPException",)

    @pytest.mark.asyncio
    async def test_alumno_no_encontrado_en_errores(self, db_session, test_tenant, test_materia):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP1 (Real)"],
            [
                ["Ana", "García", "noexiste@test.com", 80],
            ],
        )
        file = self._fake_upload("califs.xlsx", content)
        result = await CalificacionesService.preview(test_materia.id, file)
        assert result["alumnos_count"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Task 20: Tests de umbral
# ═══════════════════════════════════════════════════════════════════════════════

class TestUmbral:

    @pytest.mark.asyncio
    async def test_crear_umbral_personalizado(self, db_session, test_tenant, test_materia, test_asignacion):
        repo = UmbralMateriaRepository(db_session)
        umbral = await repo.upsert(
            asignacion_id=test_asignacion.id,
            materia_id=test_materia.id,
            tenant_id=test_tenant.id,
            umbral_pct=70,
            valores_aprobatorios=["Satisfactorio", "Excelente"],
        )
        assert umbral.umbral_pct == 70
        assert "Excelente" in umbral.valores_aprobatorios
        assert umbral.materia_id == test_materia.id

    @pytest.mark.asyncio
    async def test_actualizar_umbral_existente(self, db_session, test_tenant, test_materia, test_asignacion):
        repo = UmbralMateriaRepository(db_session)
        await repo.upsert(
            asignacion_id=test_asignacion.id,
            materia_id=test_materia.id,
            tenant_id=test_tenant.id,
            umbral_pct=70,
        )
        umbral = await repo.upsert(
            asignacion_id=test_asignacion.id,
            materia_id=test_materia.id,
            tenant_id=test_tenant.id,
            umbral_pct=65,
        )
        assert umbral.umbral_pct == 65

    @pytest.mark.asyncio
    async def test_obtener_umbral_defecto(self, db_session, test_tenant, test_materia):
        repo = UmbralMateriaRepository(db_session)
        umbral = await repo.get_by_asignacion_y_materia(
            uuid.uuid4(), test_materia.id, test_tenant.id,
        )
        assert umbral is None

    @pytest.mark.asyncio
    async def test_umbral_docente_no_afecta_otro(self, db_session, test_tenant, test_materia, mock_user):
        from app.models.rbac import Role
        from app.models.asignacion import Asignacion
        from datetime import datetime, timezone

        role = Role(name="PROFESOR")
        db_session.add(role)
        await db_session.commit()

        user_a = User(id=uuid.uuid4(), tenant_id=test_tenant.id, email="a@test.com", hashed_password="h", is_2fa_enabled=False)
        user_b = User(id=uuid.uuid4(), tenant_id=test_tenant.id, email="b@test.com", hashed_password="h", is_2fa_enabled=False)
        db_session.add_all([user_a, user_b])
        await db_session.commit()

        asig_a = Asignacion(id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=user_a.id, role_id=role.id, contexto_id=test_materia.id, desde=datetime.now(timezone.utc))
        asig_b = Asignacion(id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=user_b.id, role_id=role.id, contexto_id=test_materia.id, desde=datetime.now(timezone.utc))
        db_session.add_all([asig_a, asig_b])
        await db_session.commit()

        repo = UmbralMateriaRepository(db_session)
        await repo.upsert(asig_a.id, test_materia.id, test_tenant.id, umbral_pct=70)
        umbral_b = await repo.get_by_asignacion_y_materia(asig_b.id, test_materia.id, test_tenant.id)

        assert umbral_b is None


# ═══════════════════════════════════════════════════════════════════════════════
# Task 21: Tests de reporte de finalización
# ═══════════════════════════════════════════════════════════════════════════════

class TestReporteFinalizacion:

    def _make_xlsx(self, headers: list, rows: list[list]) -> bytes:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue()

    def _fake_upload(self, filename: str, content: bytes):
        class FakeUploadFile:
            pass
        f = FakeUploadFile()
        f.filename = filename
        f._content = content
        async def read():
            return f._content
        f.read = read
        return f

    @pytest.mark.asyncio
    async def test_detecta_entregas_sin_calificar_solo_textuales(self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP Final", "TP1 (Real)"],
            [
                ["Juan", "Pérez", "juan@test.com", "Finalizado", "Finalizado"],
            ],
        )
        file = self._fake_upload("finalizacion.xlsx", content)
        result = await CalificacionesService.preview_finalizacion(
            test_materia.id, file, db_session, mock_user,
        )

        assert "preview_token" in result
        sin_corregir = result["posibles_sin_corregir"]
        actividades = {s["actividad"] for s in sin_corregir}
        assert "TP Final" in actividades  # textual, should appear
        assert "TP1 (Real)" not in actividades  # RN-08: numeric should NOT appear

    @pytest.mark.asyncio
    async def test_no_incluye_actividades_ya_calificadas(self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user):
        repo = CalificacionesRepository(db_session)
        await repo.bulk_insert(
            [{
                "entrada_padron_id": test_entrada_padron.id,
                "materia_id": test_materia.id,
                "actividad": "TP Final",
                "nota_textual": "Satisfactorio",
                "aprobado": True,
            }],
            test_tenant.id,
            importado_por=mock_user.id,
        )
        await db_session.commit()

        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP Final"],
            [
                ["Juan", "Pérez", "juan@test.com", "Finalizado"],
            ],
        )
        file = self._fake_upload("finalizacion.xlsx", content)
        result = await CalificacionesService.preview_finalizacion(
            test_materia.id, file, db_session, mock_user,
        )

        assert len(result["posibles_sin_corregir"]) == 0

    @pytest.mark.asyncio
    async def test_no_incluye_numericas_rn08(self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP1 (Real)"],
            [
                ["Juan", "Pérez", "juan@test.com", "Finalizado"],
            ],
        )
        file = self._fake_upload("finalizacion.xlsx", content)
        result = await CalificacionesService.preview_finalizacion(
            test_materia.id, file, db_session, mock_user,
        )

        assert len(result["posibles_sin_corregir"]) == 0

    @pytest.mark.asyncio
    async def test_confirm_finalizacion_registra_audit(self, db_session, test_tenant, test_materia, test_entrada_padron, mock_user):
        content = self._make_xlsx(
            ["Nombre", "Apellido", "Email", "TP Final"],
            [
                ["Juan", "Pérez", "juan@test.com", "Finalizado"],
            ],
        )
        file = self._fake_upload("finalizacion.xlsx", content)
        preview = await CalificacionesService.preview_finalizacion(
            test_materia.id, file, db_session, mock_user,
        )
        token = preview["preview_token"]

        result = await CalificacionesService.confirm_finalizacion(db_session, token, mock_user)
        assert result["registros_detectados"] == 1

        stmt = select(AuditLog).where(AuditLog.action == "CALIFICACIONES_IMPORTAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) == 1
        assert logs[0].detalle.get("tipo") == "finalizacion"


# ═══════════════════════════════════════════════════════════════════════════════
# Task 22: Tests de vaciado scope-isolated (RN-04)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVaciadoRN04:

    @pytest.mark.asyncio
    async def test_vacia_solo_propias_calificaciones(self, db_session, test_tenant, test_materia, test_entrada_padron):
        user1 = User(id=uuid.uuid4(), tenant_id=test_tenant.id, email="u1@test.com",
                      hashed_password="h", is_2fa_enabled=False)
        user2 = User(id=uuid.uuid4(), tenant_id=test_tenant.id, email="u2@test.com",
                      hashed_password="h", is_2fa_enabled=False)
        db_session.add_all([user1, user2])
        await db_session.commit()

        repo = CalificacionesRepository(db_session)
        await repo.bulk_insert(
            [{"entrada_padron_id": test_entrada_padron.id, "materia_id": test_materia.id,
              "actividad": "TP1", "nota_numerica": 75, "aprobado": True}],
            test_tenant.id, importado_por=user1.id,
        )
        await repo.bulk_insert(
            [{"entrada_padron_id": test_entrada_padron.id, "materia_id": test_materia.id,
              "actividad": "TP2", "nota_numerica": 80, "aprobado": True}],
            test_tenant.id, importado_por=user2.id,
        )
        await db_session.commit()

        result = await CalificacionesService.vaciar_datos(db_session, test_materia.id, user1)
        assert result["eliminados_count"] == 1

        califs_u2, _ = await repo.get_by_materia(test_materia.id, test_tenant.id)
        assert len(califs_u2) == 1
        assert califs_u2[0].importado_por == user2.id

    @pytest.mark.asyncio
    async def test_sin_calificaciones_exito_sin_audit(self, db_session, test_tenant, test_materia, mock_user):
        result = await CalificacionesService.vaciar_datos(db_session, test_materia.id, mock_user)
        assert result["eliminados_count"] == 0

        stmt = select(AuditLog)
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) == 0

    @pytest.mark.asyncio
    async def test_calificaciones_otros_no_se_modifican(self, db_session, test_tenant, test_materia, test_entrada_padron):
        user1 = User(id=uuid.uuid4(), tenant_id=test_tenant.id, email="u1@test.com",
                      hashed_password="h", is_2fa_enabled=False)
        user2 = User(id=uuid.uuid4(), tenant_id=test_tenant.id, email="u2@test.com",
                      hashed_password="h", is_2fa_enabled=False)
        db_session.add_all([user1, user2])
        await db_session.commit()

        repo = CalificacionesRepository(db_session)
        await repo.bulk_insert(
            [{"entrada_padron_id": test_entrada_padron.id, "materia_id": test_materia.id,
              "actividad": "TP1", "nota_numerica": 75, "aprobado": True}],
            test_tenant.id, importado_por=user1.id,
        )
        await repo.bulk_insert(
            [{"entrada_padron_id": test_entrada_padron.id, "materia_id": test_materia.id,
              "actividad": "TP2", "nota_numerica": 80, "aprobado": True}],
            test_tenant.id, importado_por=user2.id,
        )
        await db_session.commit()

        await CalificacionesService.vaciar_datos(db_session, test_materia.id, user1)

        califs, total = await repo.get_by_materia(test_materia.id, test_tenant.id)
        assert total == 1
        assert califs[0].actividad == "TP2"


# ═══════════════════════════════════════════════════════════════════════════════
# Task 23: Tests de aislamiento multi-tenant
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiTenantIsolation:

    @pytest.mark.asyncio
    async def test_calificaciones_aisladas_por_tenant(self, db_session, test_tenant, test_materia, test_entrada_padron):
        repo = CalificacionesRepository(db_session)
        await repo.bulk_insert(
            [{"entrada_padron_id": test_entrada_padron.id, "materia_id": test_materia.id,
              "actividad": "TP1", "nota_numerica": 75, "aprobado": True}],
            test_tenant.id,
        )
        await db_session.commit()

        otro_tenant_id = uuid.uuid4()
        califs, total = await repo.get_by_materia(test_materia.id, otro_tenant_id)
        assert total == 0

    @pytest.mark.asyncio
    async def test_umbral_aislado_por_tenant(self, db_session, test_tenant, test_materia, test_asignacion):
        repo = UmbralMateriaRepository(db_session)
        await repo.upsert(
            asignacion_id=test_asignacion.id,
            materia_id=test_materia.id,
            tenant_id=test_tenant.id,
            umbral_pct=70,
        )

        otro_tenant_id = uuid.uuid4()
        umbral = await repo.get_by_asignacion_y_materia(
            test_asignacion.id, test_materia.id, otro_tenant_id,
        )
        assert umbral is None
