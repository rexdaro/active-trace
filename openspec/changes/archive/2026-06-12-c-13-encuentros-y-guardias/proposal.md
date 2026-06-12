# Proposal: C-13 — Encuentros y Guardias

## Why

Los PROFESORES planifican encuentros sincrónicos (clases virtuales) para sus comisiones pero el sistema actual no tiene modelo ni gestión de estos encuentros. El flujo es manual (publicar en el LMS uno a uno), sin generación de instancias recurrentes ni seguimiento de realización.

Además, los TUTORES registran guardias de atención a alumnos (horario, día, comisión) pero no hay trazabilidad ni visibilidad global para coordinación. Hoy no hay registro sistematizado.

**Current state**: No hay modelos SlotEncuentro, InstanciaEncuentro ni Guardia. No hay endpoints para CRUD de encuentros. No hay generación de bloque HTML para LMS embedding. No hay registro de guardias.

**Desired state**: El sistema permite crear encuentros recurrentes (slot + N instancias automáticas vía RN-13) y únicos, editar el estado de cada instancia independientemente (RN-14), generar un bloque HTML exportable para el aula virtual, proveer una vista admin transversal para COORDINADOR/ADMIN, y registrar guardias con consulta global + export.

## What Changes

1. Modelos `SlotEncuentro` (E9), `InstanciaEncuentro` (E10), `Guardia` (E11) con enums de estado.
2. Creación de encuentro recurrente (F6.1, RN-13): define slot semanal con `cant_semanas`, el sistema genera N instancias automáticamente.
3. Creación de encuentro único (F6.2): instancia sin slot padre.
4. Edición de instancia (F6.3, RN-14): estado, meet_url, video_url, comentario — independiente del slot.
5. Generación de bloque HTML para embeker en LMS (F6.4).
6. Vista admin de encuentros global (F6.5) para COORDINADOR/ADMIN.
7. Registro de guardias (F6.6): TUTOR registra propias, COORDINADOR/ADMIN consultan global + export.
8. Endpoints REST bajo `/api/v1/encuentros/*` y `/api/v1/guardias/*`.
9. Migración Alembic para tablas `slot_encuentro`, `instancia_encuentro`, `guardia`.
10. Seeds de permisos `encuentros:gestionar`, `encuentros:ver`, `guardias:registrar`, `guardias:ver`.
11. Auditoría con códigos `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR`.

## Impact

### Affected Code
- `app/models/` — nuevos `slot_encuentro.py`, `instancia_encuentro.py`, `guardia.py` con enums
- `app/schemas/` — nuevos esquemas Pydantic v2 request/response
- `app/repositories/` — nuevos `slot_encuentro.py`, `instancia_encuentro.py`, `guardia.py`
- `app/services/` — nuevos `encuentros.py`, `guardias.py`
- `app/routers/` — nuevos `encuentros.py`, `guardias.py`
- `app/db/seed.py` — agregar permisos del módulo encuentros/guardias

### API Changes
- `POST /api/v1/encuentros/slots` — crear slot recurrente + generar instancias
- `GET /api/v1/encuentros/slots` — listar slots (filtro por materia)
- `GET /api/v1/encuentros/slots/{slot_id}` — detalle de slot con instancias
- `DELETE /api/v1/encuentros/slots/{slot_id}` — eliminar slot (soft delete, instancias preservadas)
- `POST /api/v1/encuentros/instancias` — crear encuentro único
- `PATCH /api/v1/encuentros/instancias/{id}` — editar instancia (estado, meet_url, video_url, comentario)
- `GET /api/v1/encuentros/instancias` — listar instancias (filtro por materia, estado, rango fechas)
- `GET /api/v1/encuentros/instancias/{id}` — detalle de instancia
- `GET /api/v1/encuentros/export-html` — generar bloque HTML para LMS embedding
- `GET /api/v1/encuentros/admin` — vista global para COORDINADOR/ADMIN (todas las materias)
- `POST /api/v1/guardias` — registrar guardia (TUTOR)
- `GET /api/v1/guardias` — listar guardias (propio TUTOR, global COORDINADOR/ADMIN)
- `GET /api/v1/guardias/export` — exportar guardias

### RBAC
- `encuentros:gestionar` → PROFESOR (propio), COORDINADOR, ADMIN
- `encuentros:ver` → COORDINADOR, ADMIN
- `guardias:registrar` → TUTOR
- `guardias:ver` → COORDINADOR, ADMIN

### Migration Required
- [x] Database migration (`slot_encuentro`, `instancia_encuentro`, `guardia`)
- [x] Seed de permisos (`encuentros:gestionar`, `encuentros:ver`, `guardias:registrar`, `guardias:ver`)
- [ ] API version bump
- [ ] User communication needed

## Timeline Estimate

Medium (2-3 semanas). Dependencies: C-07 already done. Governance: MEDIO — implementar con checkpoints, surface decisiones de diseño.

## Risks

- [Risk] Generación de N instancias para slots largos (ej. 18 semanas) puede crear volumen alto → Mitigation: generación sincrónica en el request, es una operación rápida (solo inserts de fechas calculadas). Si escala a cientos, migrar a worker async.
- [Risk] Export HTML con contenido malicioso (XSS en títulos/URLs) → Mitigation: sanitización estricta en la generación HTML; escapar todo input del usuario.
- [Risk] Guardias sin control de duplicación (mismo tutor, mismo día, mismo horario) → Mitigation: validación de superposición en backend; no permitir dos guardias activas para el mismo asignacion_id en el mismo bloque horario.
