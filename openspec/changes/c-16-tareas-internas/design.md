# Design: Tareas Internas

## Context

El sistema trace gestiona la coordinación académica multi-tenant pero carece de un módulo formal de tareas internas. Actualmente no existe trazabilidad de asignaciones entre docentes y coordinación. Este módulo se integra al stack existente (FastAPI async, SQLAlchemy 2.0, PostgreSQL, multi-tenancy row-level, RBAC fino, auditoría).

El módulo replica el patrón establecido en avisos (C-15): modelo → repositorio → servicio → router → schemas → tests → migración → seed.

## Goals / Non-Goals

**Goals:**
- ABM completo de tareas internas con estados (Pendiente → En progreso → Resuelta/Cancelada).
- Asignación a usuario con trazabilidad de asignador y asignado.
- Hilo de comentarios por tarea (ComentarioTarea).
- Vista "mis tareas" para el docente asignado.
- Vista de administración global para coordinación con filtros (estado, materia, asignado a, asignado por, búsqueda libre).
- Delegación de tarea entre docentes.
- Soft-delete para tareas y comentarios.
- Auditoría de cada acción (crear, actualizar estado, comentar, delegar).
- Permisos finos `tareas:crear`, `tareas:ver`, `tareas:gestionar`.

**Non-Goals:**
- Notificaciones push/email al asignar tarea (se hará en integración futura con el módulo de comunicaciones).
- Adjuntos o evidencias en comentarios (solo texto plano en esta iteración).
- Workflow automático de escalamiento (la elevación a coordinación es manual).
- Tareas recurrentes o programadas.

## Decisions

1. **Modelo de datos**: Se usa `TimestampMixin` (soft-delete via `deleted_at`) y `TenantMixin` como todas las entidades del sistema. `contexto_id` como UUID nullable para referencia genérica a otra entidad del dominio (ej: materia, encuentro), sin FK explícita para mantener flexibilidad.

2. **Estados**: Se usan 4 estados del modelo de datos (Pendiente, En progreso, Resuelta, Cancelada). El FL-05 usa "Abierta" como estado inicial pero el modelo de datos dice "Pendiente" — se respeta el modelo de datos.

3. **Comentarios como tabla separada**: No se incrustan en la tarea para permitir consultas independientes, paginación y auditoría granular.

4. **Permisos**:
   - `tareas:crear` → PROFESOR, COORDINADOR (pueden crear/asignar tareas)
   - `tareas:ver` → TUTOR, PROFESOR, COORDINADOR (ver mis tareas)
   - `tareas:gestionar` → COORDINADOR, ADMIN (vista global, cambiar estado de cualquier tarea)

5. **API Structure**: Dos endpoints principales:
   - `/api/v1/tareas/mis-tareas` — para el usuario asignado (filtra por `asignado_a`).
   - `/api/v1/tareas/admin` — para coordinación (filtros combinados, sin restricción de asignado).
   - `/api/v1/tareas/{id}/comentarios` — CRUD de comentarios anidados.

6. **Delegación**: Se implementa como un UPDATE del campo `asignado_a` en la tarea, con registro en auditoría. No se crea una tabla de historial de asignaciones en esta iteración.

## Risks / Trade-offs

- **Sin historial de cambios de estado**: Los cambios de estado se auditan vía AuditLog, pero no hay una tabla específica de historial. Si en el futuro se requiere timeline visual, habrá que agregarla.
- **contexto_id sin FK**: Al ser una referencia genérica sin FK, la integridad referencial se chequea a nivel de aplicación. No hay cascade desde la entidad referenciada.
- **Sin notificaciones**: El docente asignado no recibe notificación automática. Depende de que revise su panel. Mitigación: se lista en `mis-tareas` que es la vista principal del docente.
