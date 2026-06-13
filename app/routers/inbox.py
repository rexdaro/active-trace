import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import get_current_user
from app.models.mensaje_interno import MensajeInterno
from app.models.user import Usuario
from app.schemas.inbox import MensajeResponse, MensajeSend, MensajeResponder
from app.services.audit import AuditService

router = APIRouter(prefix="/api/v1/inbox", tags=["Inbox"])


@router.get("", response_model=list[MensajeResponse])
async def list_recibidos(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = (
        select(MensajeInterno)
        .where(MensajeInterno.destinatario_id == user.id)
        .order_by(asc(MensajeInterno.leido), MensajeInterno.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/enviados", response_model=list[MensajeResponse])
async def list_enviados(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = (
        select(MensajeInterno)
        .where(MensajeInterno.remitente_id == user.id)
        .order_by(MensajeInterno.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
async def send_mensaje(
    body: MensajeSend,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = select(Usuario).where(
        Usuario.id == body.destinatario_id,
        Usuario.tenant_id == user.tenant_id,
    )
    result = await db.execute(stmt)
    destinatario = result.scalar_one_or_none()
    if not destinatario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario no encontrado o no pertenece al mismo tenant",
        )

    mensaje = MensajeInterno(
        tenant_id=user.tenant_id,
        remitente_id=user.id,
        destinatario_id=body.destinatario_id,
        asunto=body.asunto,
        cuerpo=body.cuerpo,
    )
    db.add(mensaje)
    await db.commit()
    await db.refresh(mensaje)

    await AuditService.log_action(
        db=db,
        action="MENSAJE_ENVIAR",
        user_id=str(user.id),
        resource="mensaje_interno",
        status="success",
        actor_id=str(user.id),
        detalle={"destinatario_id": str(body.destinatario_id), "asunto": body.asunto},
    )

    return mensaje


@router.post("/{mensaje_id}/responder", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
async def responder_mensaje(
    mensaje_id: uuid.UUID,
    body: MensajeResponder,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = select(MensajeInterno).where(MensajeInterno.id == mensaje_id)
    result = await db.execute(stmt)
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje original no encontrado")

    hilo_id = original.hilo_id or original.id

    respuesta = MensajeInterno(
        tenant_id=user.tenant_id,
        remitente_id=user.id,
        destinatario_id=original.remitente_id,
        asunto=f"Re: {original.asunto}",
        cuerpo=body.cuerpo,
        hilo_id=hilo_id,
    )
    db.add(respuesta)
    await db.commit()
    await db.refresh(respuesta)

    await AuditService.log_action(
        db=db,
        action="MENSAJE_ENVIAR",
        user_id=str(user.id),
        resource="mensaje_interno",
        status="success",
        actor_id=str(user.id),
        detalle={"tipo": "respuesta", "hilo_id": str(hilo_id), "responde_a": str(mensaje_id)},
    )

    return respuesta


@router.put("/{mensaje_id}/leer", response_model=MensajeResponse)
async def marcar_leido(
    mensaje_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = select(MensajeInterno).where(
        MensajeInterno.id == mensaje_id,
        MensajeInterno.destinatario_id == user.id,
    )
    result = await db.execute(stmt)
    mensaje = result.scalar_one_or_none()
    if not mensaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje no encontrado")

    mensaje.leido = True
    await db.commit()
    await db.refresh(mensaje)
    return mensaje
