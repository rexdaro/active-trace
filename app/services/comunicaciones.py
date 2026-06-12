import uuid
import time
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, StrictUndefined

from app.repositories.comunicaciones import ComunicacionesRepository
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.models.padron import EntradaPadron
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.services.audit import AuditService
from app.schemas.comunicacion import (
    PreviewRequest,
    PreviewResponse,
    PreviewItem,
    ConfirmRequest,
    ConfirmResponse,
    LoteSummary,
    LoteListResponse,
    ComunicacionRead,
    LoteDetailResponse,
    AprobarLoteResponse,
    AprobarIndividualResponse,
    RechazarLoteResponse,
    CancelarResponse,
    EstadoPanelItem,
    EstadosPanelResponse,
)


class ComunicacionesService:
    _preview_store: dict[str, dict] = {}
    PREVIEW_TTL = 900

    @staticmethod
    def _render_template(template_str: str, variables: dict) -> str:
        env = Environment(undefined=StrictUndefined)
        tpl = env.from_string(template_str)
        return tpl.render(**variables)

    @staticmethod
    def _build_variables(entrada: EntradaPadron, materia_nombre: str) -> dict:
        nombre_completo = f"{entrada.nombre} {entrada.apellidos}".strip()
        return {
            "nombre": entrada.nombre,
            "apellidos": entrada.apellidos,
            "nombre_completo": nombre_completo,
            "email": entrada.email,
            "materia": materia_nombre,
        }

    @staticmethod
    async def preview(
        db: AsyncSession,
        request: PreviewRequest,
        user: User,
    ) -> PreviewResponse:
        stmt = select(EntradaPadron).where(
            EntradaPadron.id.in_(request.destinatarios),
            EntradaPadron.tenant_id == user.tenant_id,
        )
        result = await db.execute(stmt)
        entradas = list(result.scalars().all())

        encontrados = {e.id for e in entradas}
        solicitados = set(request.destinatarios)
        no_encontrados = solicitados - encontrados

        errores = [f"EntradaPadron {eid} no encontrada" for eid in no_encontrados]

        materia_stmt = select(Materia).where(Materia.id == request.materia_id)
        materia_result = await db.execute(materia_stmt)
        materia = materia_result.scalar_one_or_none()
        materia_nombre = materia.name if materia else ""

        items = []
        for entrada in entradas:
            variables = ComunicacionesService._build_variables(entrada, materia_nombre)
            asunto_rend = ComunicacionesService._render_template(request.asunto, variables)
            cuerpo_rend = ComunicacionesService._render_template(request.cuerpo, variables)
            items.append(PreviewItem(
                entrada_padron_id=entrada.id,
                destinatario=entrada.email,
                nombre=entrada.nombre,
                asunto_renderizado=asunto_rend,
                cuerpo_renderizado=cuerpo_rend,
            ))

        token = str(uuid.uuid4())
        ComunicacionesService._preview_store[token] = {
            "items": [
                {
                    "entrada_padron_id": str(i.entrada_padron_id),
                    "destinatario": i.destinatario,
                    "nombre": i.nombre,
                    "asunto_renderizado": i.asunto_renderizado,
                    "cuerpo_renderizado": i.cuerpo_renderizado,
                }
                for i in items
            ],
            "materia_id": str(request.materia_id),
            "asunto_template": request.asunto,
            "cuerpo_template": request.cuerpo,
            "timestamp": time.time(),
        }

        return PreviewResponse(
            preview_token=token,
            items=items,
            total=len(items),
            errores=errores,
        )

    @staticmethod
    async def confirm(
        db: AsyncSession,
        request: ConfirmRequest,
        user: User,
    ) -> ConfirmResponse:
        data = ComunicacionesService._preview_store.pop(request.preview_token, None)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de preview inválido o expirado",
            )

        if time.time() - data["timestamp"] > ComunicacionesService.PREVIEW_TTL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de preview expirado",
            )

        materia_id = uuid.UUID(data["materia_id"])

        tenant_stmt = select(Tenant).where(Tenant.id == user.tenant_id)
        tenant_result = await db.execute(tenant_stmt)
        tenant = tenant_result.scalar_one()
        requiere_aprobacion = tenant.requiere_aprobacion

        lote_id = uuid.uuid4()
        repo = ComunicacionesRepository(db)

        bulk_data = []
        for item in data["items"]:
            bulk_data.append({
                "tenant_id": user.tenant_id,
                "enviado_por": user.id,
                "materia_id": materia_id,
                "destinatario": item["destinatario"],
                "asunto": item["asunto_renderizado"],
                "cuerpo": item["cuerpo_renderizado"],
                "estado": ComunicacionEstado.PENDIENTE.value,
                "lote_id": lote_id,
                "lote_aprobado": False,
            })

        await repo.bulk_create(bulk_data)

        await AuditService.log_action(
            db=db,
            action="COMUNICACION_ENVIAR",
            user_id=str(user.id),
            resource="comunicaciones",
            status="success",
            actor_id=str(user.id),
            materia_id=str(materia_id),
            detalle={
                "lote_id": str(lote_id),
                "requiere_aprobacion": requiere_aprobacion,
                "cantidad": len(bulk_data),
            },
            filas_afectadas=len(bulk_data),
        )

        return ConfirmResponse(
            lote_id=lote_id,
            cantidad=len(bulk_data),
            requiere_aprobacion=requiere_aprobacion,
        )

    @staticmethod
    async def aprobar_lote(
        db: AsyncSession,
        lote_id: uuid.UUID,
        user: User,
    ) -> AprobarLoteResponse:
        repo = ComunicacionesRepository(db)
        transicionados = await repo.approve_by_lote(lote_id, user.tenant_id)

        if transicionados > 0:
            comunicaciones = await repo.get_by_lote(lote_id, user.tenant_id)
            materia_id = str(comunicaciones[0].materia_id) if comunicaciones else None

            await AuditService.log_action(
                db=db,
                action="COMUNICACION_APROBAR",
                user_id=str(user.id),
                resource="comunicaciones",
                status="success",
                actor_id=str(user.id),
                materia_id=materia_id,
                detalle={"lote_id": str(lote_id), "tipo": "lote"},
                filas_afectadas=transicionados,
            )

        return AprobarLoteResponse(
            lote_id=lote_id,
            transicionados=transicionados,
        )

    @staticmethod
    async def aprobar_individual(
        db: AsyncSession,
        comunicacion_id: uuid.UUID,
        user: User,
    ) -> AprobarIndividualResponse:
        repo = ComunicacionesRepository(db)
        comunicacion = await repo.approve_single(comunicacion_id, user.tenant_id)

        if comunicacion is not None:
            estado = comunicacion.estado
            await AuditService.log_action(
                db=db,
                action="COMUNICACION_APROBAR",
                user_id=str(user.id),
                resource="comunicaciones",
                status="success",
                actor_id=str(user.id),
                materia_id=str(comunicacion.materia_id),
                detalle={"comunicacion_id": str(comunicacion_id), "tipo": "individual"},
                filas_afectadas=1,
            )
        else:
            query = select(Comunicacion).where(
                Comunicacion.id == comunicacion_id,
                Comunicacion.tenant_id == user.tenant_id,
            )
            result = await db.execute(query)
            comunicacion = result.scalar_one_or_none()
            estado = comunicacion.estado if comunicacion else ComunicacionEstado.PENDIENTE.value

        return AprobarIndividualResponse(
            id=comunicacion_id,
            estado=estado,
        )

    @staticmethod
    async def rechazar_lote(
        db: AsyncSession,
        lote_id: uuid.UUID,
        user: User,
    ) -> RechazarLoteResponse:
        repo = ComunicacionesRepository(db)
        cancelados = await repo.cancel_by_lote(lote_id, user.tenant_id)

        if cancelados > 0:
            comunicaciones = await repo.get_by_lote(lote_id, user.tenant_id)
            materia_id = str(comunicaciones[0].materia_id) if comunicaciones else None

            await AuditService.log_action(
                db=db,
                action="COMUNICACION_CANCELAR",
                user_id=str(user.id),
                resource="comunicaciones",
                status="success",
                actor_id=str(user.id),
                materia_id=materia_id,
                detalle={"lote_id": str(lote_id), "tipo": "lote"},
                filas_afectadas=cancelados,
            )

        return RechazarLoteResponse(
            lote_id=lote_id,
            cancelados=cancelados,
        )

    @staticmethod
    async def cancelar_individual(
        db: AsyncSession,
        comunicacion_id: uuid.UUID,
        user: User,
    ) -> CancelarResponse:
        repo = ComunicacionesRepository(db)
        comunicacion = await repo.transition_state(
            comunicacion_id,
            ComunicacionEstado.PENDIENTE.value,
            ComunicacionEstado.CANCELADO.value,
            user.tenant_id,
        )

        if comunicacion is not None:
            await AuditService.log_action(
                db=db,
                action="COMUNICACION_CANCELAR",
                user_id=str(user.id),
                resource="comunicaciones",
                status="success",
                actor_id=str(user.id),
                materia_id=str(comunicacion.materia_id),
                detalle={"comunicacion_id": str(comunicacion_id), "tipo": "individual"},
                filas_afectadas=1,
            )
            return CancelarResponse(id=comunicacion_id, estado=comunicacion.estado)

        query = select(Comunicacion).where(
            Comunicacion.id == comunicacion_id,
            Comunicacion.tenant_id == user.tenant_id,
        )
        result = await db.execute(query)
        comunicacion = result.scalar_one_or_none()
        estado = comunicacion.estado if comunicacion else ComunicacionEstado.PENDIENTE.value
        return CancelarResponse(id=comunicacion_id, estado=estado)

    @staticmethod
    async def get_lotes(
        db: AsyncSession,
        materia_id: uuid.UUID | None,
        user: User,
        offset: int = 0,
        limit: int = 50,
    ) -> LoteListResponse:
        repo = ComunicacionesRepository(db)
        lotes_data, total = await repo.get_lotes(user.tenant_id, materia_id, offset, limit)
        lotes = [LoteSummary(**l) for l in lotes_data]
        return LoteListResponse(lotes=lotes, total=total)

    @staticmethod
    async def get_lote_detalle(
        db: AsyncSession,
        lote_id: uuid.UUID,
        user: User,
    ) -> LoteDetailResponse:
        repo = ComunicacionesRepository(db)
        lote_dict = await repo.get_lote_summary(lote_id, user.tenant_id)
        if lote_dict is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lote no encontrado",
            )

        comunicaciones = await repo.get_by_lote(lote_id, user.tenant_id)
        return LoteDetailResponse(
            lote=LoteSummary(**lote_dict),
            comunicaciones=[ComunicacionRead.model_validate(c) for c in comunicaciones],
        )

    @staticmethod
    async def get_estados_panel(
        db: AsyncSession,
        materia_id: uuid.UUID | None,
        user: User,
    ) -> EstadosPanelResponse:
        repo = ComunicacionesRepository(db)
        panel_data = await repo.get_estados_panel(user.tenant_id, materia_id)
        items = [EstadoPanelItem(**p) for p in panel_data]
        return EstadosPanelResponse(items=items)
