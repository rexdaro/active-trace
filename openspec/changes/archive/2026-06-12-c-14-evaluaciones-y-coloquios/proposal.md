# Proposal: C-14 — Evaluaciones y Coloquios

## Why

Los COORDINADORES y PROFESORES necesitan crear convocatorias de coloquio (evaluaciones orales) con días y cupos disponibles, importar el padrón de alumnos habilitados, y que los ALUMNOS puedan reservar turno en un día con cupo. Hoy no hay modelo ni endpoints para gestionar evaluaciones orales, reservas ni registro de notas.

**Current state**: No hay modelos `Evaluacion`, `ReservaEvaluacion` ni `ResultadoEvaluacion`. No hay endpoints para crear convocatorias, importar alumnos ni gestionar reservas. Las evaluaciones orales se coordinan fuera del sistema.

**Desired state**: El sistema permite crear convocatorias de coloquio con días y cupos (F7.3), importar el padrón de alumnos habilitados (F7.2), listar convocatorias con métricas operativas (F7.4), que los ALUMNOS reserven turno en días con cupo (FL-07), cancelen su reserva, y que COORDINADOR/ADMIN tengan un panel de métricas (F7.1) y administración global con registro de notas (F7.5).

## What Changes

1. Modelos `Evaluacion` (E14), `ReservaEvaluacion` (E14), `ResultadoEvaluacion` (E14) con enums `TipoEvaluacion` (Parcial | TP | Coloquio | Recuperatorio) y `EstadoReserva` (Activa | Cancelada).
2. Creación de convocatoria de coloquio (F7.3): define materia, instancia, días disponibles y cupo por día.
3. Importar alumnos a convocatoria (F7.2): carga/actualiza el padrón de alumnos habilitados para una evaluacion específica mediante `EntradaPadron`.
4. Listado de convocatorias (F7.4): vista tabular con materia, instancia, días, convocados, reservas activas, cupos libres.
5. Panel de métricas (F7.1): total alumnos cargados, instancias activas, reservas activas, notas registradas.
6. Admin global (F7.5): gestión de convocatorias (alta, edición, cierre), registro académico consolidado de resultados, agenda de reservas activas.
7. Reserva de turno por ALUMNO (FL-07): día disponible con cupo → reserva Activa. Cancelación voluntaria libera el cupo.
8. Endpoints REST bajo `/api/v1/coloquios/*` con permisos diferenciados.
9. Migración Alembic para tablas `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion`.
10. Seeds de permisos `coloquios:gestionar`, `coloquios:reservar`, `coloquios:ver`.

## Impact

### Affected Code
- `app/models/` — nuevos `evaluacion.py` con enums `TipoEvaluacion`, `EstadoReserva`
- `app/schemas/` — nuevos esquemas Pydantic v2 request/response
- `app/repositories/` — nuevo `coloquios.py`
- `app/services/` — nuevo `coloquios.py`
- `app/routers/` — nuevo `coloquios.py`
- `app/db/seed.py` — agregar permisos del módulo coloquios

### API Changes
- `POST /api/v1/coloquios` — crear convocatoria (F7.3)
- `POST /api/v1/coloquios/{id}/alumnos` — importar alumnos a convocatoria (F7.2)
- `GET /api/v1/coloquios` — listar convocatorias con métricas (F7.4)
- `GET /api/v1/coloquios/{id}` — detalle de convocatoria
- `GET /api/v1/coloquios/metricas` — panel de métricas (F7.1)
- `GET /api/v1/coloquios/admin` — admin global (F7.5)
- `POST /api/v1/coloquios/{id}/reservar` — reservar turno (ALUMNO, FL-07)
- `POST /api/v1/coloquios/{id}/cancelar` — cancelar reserva
- `POST /api/v1/coloquios/{id}/resultados` — registrar nota final (F7.5)
- `GET /api/v1/coloquios/{id}/resultados` — consultar resultados consolidados

### RBAC
- `coloquios:gestionar` → COORDINADOR, ADMIN
- `coloquios:reservar` → ALUMNO
- `coloquios:ver` → COORDINADOR, ADMIN, PROFESOR (de su materia)

### Migration Required
- [x] Database migration (`evaluacion`, `reserva_evaluacion`, `resultado_evaluacion`)
- [x] Seed de permisos (`coloquios:gestionar`, `coloquios:reservar`, `coloquios:ver`)
- [ ] API version bump
- [ ] User communication needed

## Timeline Estimate

Medium (2-3 semanas). Dependencies: C-07 already done. Governance: MEDIO — implementar con checkpoints, surface decisiones de diseño.

## Risks

- [Risk] Race condition en reserva del último cupo (dos ALUMNOS reservan simultáneamente el mismo día) → Mitigation: reserva con lock optimista o `SELECT ... FOR UPDATE` en la transacción de creación de `ReservaEvaluacion`.
- [Risk] Importación de alumnos duplicados (mismo alumno importado dos veces a la misma convocatoria) → Mitigation: unique constraint `(evaluacion_id, alumno_id)` y upsert en el import.
- [Risk] Cancelación de reserva que libera cupo ya tomado por agenda → Mitigation: la liberación es automática al cambiar estado a Cancelada; el cupo se recalcula contando solo reservas Activas.
