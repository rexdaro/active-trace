# Proposal: c-16-tareas-internas

## Why

El sistema carece de un mecanismo formal de coordinación interna entre docentes y coordinación. Actualmente no hay trazabilidad de tareas asignadas entre roles del equipo académico, lo que obliga a usar canales externos (mail, WhatsApp) sin registro auditado. Este módulo resuelve el vacío con un workflow completo de tareas internas con estados, comentarios y seguimiento multi-tenant.

## What Changes

1.  Nuevo modelo `Tarea` con estados (Pendiente, En progreso, Resuelta, Cancelada) y asignación a usuario.
2.  Nuevo modelo `ComentarioTarea` para el hilo de comentarios en cada tarea.
3.  CRUD completo de tareas con endpoints separados por perfil:
    - `mis-tareas` — vista del docente asignado.
    - `admin-tareas` — vista global de coordinación con filtros.
4.  Delegación de tareas entre docentes con trazabilidad (asignador/originador).
5.  Permisos finos (`tareas:crear`, `tareas:ver`, `tareas:gestionar`) registrados en seed.
6.  Auditoría completa de cada acción sobre tareas y comentarios.

## Capabilities

### New Capabilities
- `tareas-internas`: ABM completo de tareas internas con asignación a usuario, estados, comentarios, delegación, vista por docente y vista global de administración con filtros.

### Modified Capabilities
- Ninguna. Es un módulo nuevo sin cambios sobre capacidades existentes.

## Impact

- **Database**: Nuevas tablas `tareas` y `comentarios_tarea`.
- **Models**: Nuevos archivos `app/models/tarea.py`, registrado en `app/models/__init__.py`.
- **Repository**: Nuevo `app/repositories/tareas.py`.
- **Service**: Nuevo `app/services/tareas.py`.
- **Router**: Nuevo `app/routers/tareas.py`, registrado en `app/main.py` o `app/routers/__init__.py`.
- **Schemas**: Nuevo `app/schemas/tarea.py`.
- **Seed**: Nuevos permisos `tareas:crear`, `tareas:ver`, `tareas:gestionar` en `app/db/seed.py`.
- **Tests**: 4 archivos de test: `test_tarea_model.py`, `test_tarea_repo.py`, `test_tarea_service.py`, `test_tareas_router.py`.
- **Migration**: Una migración Alembic con las tablas `tareas` y `comentarios_tarea`.
