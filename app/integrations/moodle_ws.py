import uuid
import hashlib
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from fastapi import HTTPException, status

from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.user import User, Usuario
from app.models.padron import VersionPadron, EntradaPadron
from app.repositories.padron import PadronRepository
from app.services.audit import AuditService


class MoodleWSService:

    @staticmethod
    async def _get_tenant_config(db: AsyncSession, tenant_id: uuid.UUID) -> tuple[str | None, str | None]:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            return None, None
        return tenant.moodle_ws_url, tenant.moodle_token

    @staticmethod
    async def _call_moodle(method: str, base_url: str, token: str, params: dict | None = None) -> dict:
        url = f"{base_url.rstrip('/')}/webservice/rest/server.php"
        if params is None:
            params = {}
        params.update({
            "wstoken": token,
            "wsfunction": method,
            "moodlewsrestformat": "json",
        })

        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, data=params)
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Moodle WS no disponible después de 3 intentos: {last_error}",
        )

    @staticmethod
    async def get_participants(base_url: str, token: str, course_id: int) -> list[dict]:
        data = await MoodleWSService._call_moodle("core_enrol_get_enrolled_users", base_url, token, {"courseid": course_id})
        participants = []
        for u in data:
            participants.append({
                "nombre": u.get("firstname", ""),
                "apellidos": u.get("lastname", ""),
                "email": u.get("email", ""),
                "id": str(u.get("id", "")),
            })
        return participants

    @staticmethod
    async def get_activities(base_url: str, token: str, course_id: int) -> list[dict]:
        data = await MoodleWSService._call_moodle("core_course_get_contents", base_url, token, {"courseid": course_id})
        activities = []
        for section in data:
            for module in section.get("modules", []):
                activities.append({
                    "id": str(module.get("id", "")),
                    "name": module.get("name", ""),
                    "modname": module.get("modname", ""),
                })
        return activities

    @staticmethod
    async def sync_from_moodle(db: AsyncSession, user: User, materia_id: uuid.UUID | None = None) -> dict:
        base_url, token = await MoodleWSService._get_tenant_config(db, user.tenant_id)
        if not base_url or not token:
            return {"status": "skipped", "materias_procesadas": 0, "errores": ["Tenant sin configuración Moodle WS"]}

        query = select(Materia).where(
            Materia.tenant_id == user.tenant_id,
            Materia.deleted_at.is_(None),
            Materia.is_active == True,
        )
        if materia_id:
            query = query.where(Materia.id == materia_id)

        result = await db.execute(query)
        materias = list(result.scalars().all())

        procesadas = 0
        errores = []
        repo = PadronRepository(db)

        for materia in materias:
            try:
                participants = await MoodleWSService.get_participants(base_url, token, int(materia.code))
            except HTTPException as e:
                errores.append(f"Materia {materia.id}: {e.detail}")
                continue
            except Exception as e:
                errores.append(f"Materia {materia.id}: {str(e)}")
                continue

            cohorte_id = uuid.uuid4()

            raw = f"{datetime.now(timezone.utc).isoformat()}{materia.id}{user.tenant_id}"
            file_hash = hashlib.sha256(raw.encode()).hexdigest()

            await repo.desactivar_anterior(materia.id, cohorte_id, user.tenant_id)

            version = await repo.crear_version(
                tenant_id=user.tenant_id,
                materia_id=materia.id,
                cohorte_id=cohorte_id,
                archivo_nombre="moodle-sync",
                archivo_hash=file_hash,
                origen="MoodleWS",
                cargado_por=user.id,
                activa=True,
            )

            email_map = {}
            usuarios_stmt = select(Usuario).where(
                Usuario.tenant_id == user.tenant_id,
                Usuario.deleted_at.is_(None),
            )
            usuarios_result = await db.execute(usuarios_stmt)
            for u in list(usuarios_result.scalars().all()):
                email_map[u.email] = u.id

            entradas = []
            for p in participants:
                entrada = EntradaPadron(
                    version_id=version.id,
                    tenant_id=user.tenant_id,
                    usuario_id=email_map.get(p["email"]),
                    nombre=p["nombre"],
                    apellidos=p["apellidos"],
                    email=p["email"],
                )
                db.add(entrada)
                entradas.append(entrada)

            await db.commit()

            await AuditService.log_action(
                db=db,
                action="PADRON_CARGAR",
                user_id=str(user.id),
                resource="padron",
                status="success",
                actor_id=str(user.id),
                materia_id=str(materia.id),
                detalle={"origen": "MoodleWS", "materia_id": str(materia.id)},
                filas_afectadas=len(entradas),
            )

            procesadas += 1

        return {"status": "completed", "materias_procesadas": procesadas, "errores": errores}
