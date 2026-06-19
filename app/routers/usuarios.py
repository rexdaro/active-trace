import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import check_permission, get_current_user
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role
from app.schemas.usuario import UserCreate, UserRead
import bcrypt

router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


@router.get("/roles")
async def listar_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Role).order_by(Role.name))
    roles = result.scalars().all()
    return [{"id": r.id, "name": r.name} for r in roles]


@router.get("")
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    estado: str = "activos",
):
    stmt = select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))
    if estado == "activos":
        stmt = stmt.where(User.activo == True)
    elif estado == "inactivos":
        stmt = stmt.where(User.activo == False)
    result = await db.execute(stmt)
    users = result.scalars().all()
    data = []
    for u in users:
        roles = [ur.role.name for ur in u.user_roles if ur.role]
        data.append({
            "id": str(u.id),
            "nombre": u.nombre or (u.email.split("@")[0] if "@" in u.email else u.email),
            "email": u.email,
            "roles": roles,
            "activo": u.activo,
        })
    return data


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def crear_usuario_admin(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    hashed = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode()
    user = User(
        tenant_id=current_user.tenant_id,
        email=body.email,
        hashed_password=hashed,
        dni=body.dni,
        cuil=body.cuil,
        cbu=body.cbu,
        nombre=body.nombre,
        datos_fiscales=body.datos_fiscales,
        datos_bancarios=body.datos_bancarios,
        regional=body.regional,
        modalidad_cobro=body.modalidad_cobro,
    )
    db.add(user)
    await db.flush()

    role_id = body.role_id
    if role_id is not None:
        role_result = await db.execute(select(Role).where(Role.id == role_id))
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol id={role_id} no encontrado")
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
    else:
        alumno_result = await db.execute(select(Role).where(Role.name == "ALUMNO"))
        alumno = alumno_result.scalar_one_or_none()
        if alumno:
            user_role = UserRole(user_id=user.id, role_id=alumno.id)
            db.add(user_role)

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}")
async def obtener_usuario(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": str(user.id),
        "email": user.email,
        "nombre": user.nombre,
        "dni": user.dni,
        "cuil": user.cuil,
        "cbu": user.cbu,
        "datos_fiscales": user.datos_fiscales,
        "datos_bancarios": user.datos_bancarios,
        "regional": user.regional,
        "modalidad_cobro": user.modalidad_cobro,
        "roles": [{"id": ur.role.id, "name": ur.role.name} for ur in user.user_roles if ur.role],
    }


@router.put("/{user_id}")
async def actualizar_usuario(
    user_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    campos = ["nombre", "email", "dni", "cuil", "cbu", "datos_fiscales", "datos_bancarios", "regional", "modalidad_cobro"]
    for campo in campos:
        if campo in body:
            setattr(user, campo, body[campo])

    if "password" in body and body["password"]:
        hashed = bcrypt.hashpw(body["password"].encode("utf-8"), bcrypt.gensalt()).decode()
        user.hashed_password = hashed

    await db.commit()
    return {"ok": True, "mensaje": "Usuario actualizado correctamente"}


@router.put("/{user_id}/toggle-activo")
async def toggle_activo(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.activo = not user.activo
    await db.commit()
    return {"ok": True, "activo": user.activo, "mensaje": f"Usuario {'activado' if user.activo else 'desactivado'} correctamente"}


@router.post("/{user_id}/roles")
async def asignar_rol(
    user_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rol_nombre = body.get("rol")
    if not rol_nombre:
        raise HTTPException(status_code=400, detail="Falta 'rol' en el body")

    result = await db.execute(select(Role).where(Role.name == rol_nombre.upper()))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol '{rol_nombre}' no encontrado")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    existing = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
        )
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "mensaje": f"El usuario ya tiene el rol '{rol_nombre}'"}

    user_role = UserRole(user_id=user_id, role_id=role.id)
    db.add(user_role)
    await db.commit()
    return {"ok": True, "mensaje": f"Rol '{rol_nombre}' asignado correctamente"}


@router.delete("/{user_id}/roles/{role_id}")
async def remover_rol(
    user_id: uuid.UUID,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        raise HTTPException(status_code=404, detail="El usuario no tiene ese rol asignado")

    await db.delete(user_role)
    await db.commit()
    return {"ok": True, "mensaje": "Rol removido correctamente"}
