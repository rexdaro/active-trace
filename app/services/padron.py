import uuid
import io
import os
import hashlib
import csv
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import openpyxl

from app.repositories.padron import PadronRepository
from app.models.padron import EntradaPadron, VersionPadron
from app.models.user import User
from app.services.audit import AuditService


_preview_store: dict[str, dict] = {}

EXPECTED_COLUMNS = {"nombre", "apellidos", "email", "comision", "regional"}
ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class PadronService:

    @staticmethod
    def _detect_csv_delimiter(head: str) -> str:
        comma = head.count(",")
        semicolon = head.count(";")
        return ";" if semicolon > comma else ","

    @staticmethod
    def _parse_xlsx(content: bytes) -> tuple[list[dict], list[str], list[str]]:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        if not rows:
            return [], [], ["Archivo vacío"]

        raw_headers = [str(h).strip().lower() if h is not None else "" for h in rows[0]]
        columnas_detectadas = [c for c in raw_headers if c in EXPECTED_COLUMNS]
        col_indices = {col: idx for idx, col in enumerate(raw_headers) if col in EXPECTED_COLUMNS}

        entries = []
        errors = []
        for row_idx, row in enumerate(rows[1:], start=2):
            if all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            entry = {"nombre": "", "apellidos": "", "email": "", "comision": None, "regional": None}
            for col, idx in col_indices.items():
                val = str(row[idx]).strip() if idx < len(row) and row[idx] is not None else ""
                if col == "email":
                    entry[col] = val
                elif col in ("comision", "regional"):
                    entry[col] = val or None
                else:
                    entry[col] = val
            if not entry["email"]:
                errors.append(f"Fila {row_idx}: email vacío, se omite")
                continue
            entries.append(entry)

        return entries, columnas_detectadas, errors

    @staticmethod
    def _parse_csv(content: bytes) -> tuple[list[dict], list[str], list[str]]:
        text = content.decode("utf-8-sig")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        delimiter = PadronService._detect_csv_delimiter(first_line)

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower() if f else f for f in reader.fieldnames]

        columnas_detectadas = [c for c in reader.fieldnames if c in EXPECTED_COLUMNS] if reader.fieldnames else []
        entries = []
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            if all(not (row.get(k) or "").strip() for k in EXPECTED_COLUMNS):
                continue
            entry = {"nombre": (row.get("nombre") or "").strip(),
                     "apellidos": (row.get("apellidos") or "").strip(),
                     "email": (row.get("email") or "").strip(),
                     "comision": (row.get("comision") or "").strip() or None,
                     "regional": (row.get("regional") or "").strip() or None}
            if not entry["email"]:
                errors.append(f"Fila {row_idx}: email vacío, se omite")
                continue
            entries.append(entry)

        return entries, columnas_detectadas, errors

    @staticmethod
    async def preview(file: UploadFile, materia_id: uuid.UUID, cohorte_id: uuid.UUID) -> dict:
        ext = os.path.splitext(file.filename or "archivo")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no soportado: {ext}. Formatos aceptados: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB",
            )

        file_hash = hashlib.sha256(content).hexdigest()

        if ext == ".xlsx":
            entries, columns, errors = PadronService._parse_xlsx(content)
        else:
            entries, columns, errors = PadronService._parse_csv(content)

        token = str(uuid.uuid4())
        _preview_store[token] = {
            "entries": entries,
            "materia_id": str(materia_id),
            "cohorte_id": str(cohorte_id),
            "archivo_nombre": file.filename or "archivo",
            "archivo_hash": file_hash,
        }

        return {
            "preview_token": token,
            "columnas_detectadas": columns,
            "filas_count": len(entries),
            "errores": errors,
        }

    @staticmethod
    async def _get_usuarios_by_emails(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, uuid.UUID]:
        stmt = select(User).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
        result = await db.execute(stmt)
        usuarios = list(result.scalars().all())
        return {u.email: u.id for u in usuarios}

    @staticmethod
    async def confirm(db: AsyncSession, preview_token: str, user: User) -> dict:
        data = _preview_store.pop(preview_token, None)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de preview inválido o expirado",
            )

        materia_id = uuid.UUID(data["materia_id"])
        cohorte_id = uuid.UUID(data["cohorte_id"])
        repo = PadronRepository(db)

        existing = await repo.get_version_by_hash(data["archivo_hash"], materia_id, cohorte_id, user.tenant_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una versión con el mismo contenido para esta materia y cohorte",
            )

        await repo.desactivar_anterior(materia_id, cohorte_id, user.tenant_id)

        version = await repo.crear_version(
            tenant_id=user.tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            archivo_nombre=data["archivo_nombre"],
            archivo_hash=data["archivo_hash"],
            origen="Archivo",
            cargado_por=user.id,
            activa=True,
        )

        email_map = await PadronService._get_usuarios_by_emails(db, user.tenant_id)

        entradas = []
        for e in data["entries"]:
            entrada = EntradaPadron(
                version_id=version.id,
                tenant_id=user.tenant_id,
                usuario_id=email_map.get(e["email"]),
                nombre=e["nombre"],
                apellidos=e["apellidos"],
                email=e["email"],
                comision=e.get("comision"),
                regional=e.get("regional"),
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
            materia_id=str(materia_id),
            detalle={"version_id": str(version.id), "materia_id": str(materia_id), "cohorte_id": str(cohorte_id)},
            filas_afectadas=len(entradas),
        )

        return {"version_id": version.id, "entradas_count": len(entradas)}

    @staticmethod
    async def vaciar_datos(db: AsyncSession, materia_id: uuid.UUID, user: User) -> dict:
        repo = PadronRepository(db)
        eliminadas = await repo.vaciar_datos_usuario(materia_id, user.id, user.tenant_id)

        if eliminadas > 0:
            await AuditService.log_action(
                db=db,
                action="PADRON_CARGAR",
                user_id=str(user.id),
                resource="padron",
                status="success",
                actor_id=str(user.id),
                materia_id=str(materia_id),
                detalle={"materia_id": str(materia_id), "action": "vaciar"},
                filas_afectadas=eliminadas,
            )

        return {"eliminadas": eliminadas}

    @staticmethod
    @staticmethod
    async def get_alumnos_by_materia(db: AsyncSession, materia_id: uuid.UUID, user: User) -> list[dict]:
        stmt = (
            select(EntradaPadron)
            .join(VersionPadron, EntradaPadron.version_id == VersionPadron.id)
            .where(
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa == True,
                VersionPadron.tenant_id == user.tenant_id,
            )
        )
        result = await db.execute(stmt)
        entradas = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "nombre": e.nombre,
                "apellidos": e.apellidos,
                "email": e.email,
            }
            for e in entradas
        ]

    @staticmethod
    async def get_versiones(db: AsyncSession, materia_id: uuid.UUID, user: User) -> list:
        repo = PadronRepository(db)
        return await repo.get_versiones_materia(materia_id, user.tenant_id)
