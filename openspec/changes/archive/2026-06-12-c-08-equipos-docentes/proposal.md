# Proposal: C-08 — Equipos Docentes

## Why

Activia-Trace necesita que coordinadores y administradores puedan **armar y gestionar equipos docentes** por materia×carrera×cohorte: asignar docentes en bloque, clonar el equipo de un período al siguiente, modificar vigencias y exportar el equipo. Sin esto, cada inicio de cuatrimestre exige reasignar manualmente a cada docente — una tarea que escala mal con el número de comisiones.

**Context**: El modelo `Asignacion` ya existe (C-07). Tiene `user_id`, `role_id`, `contexto_id`, `responsable_id`, `desde`, `hasta` y `tenant_id`. No se necesitan tablas nuevas. Lo que falta son las **operaciones de gestión sobre el conjunto** del equipo: masiva, clonado, vigencia en bloque, export.

**Current state**: Solo existe `POST /api/asignaciones` (una asignación por request). No hay endpoints para operaciones batch, no hay forma de consultar "mis equipos" como docente autenticado, no hay clonado entre cohortes, no hay export.

**Desired state**: El sistema expone `/api/equipos/*` con 5 endpoints que cubren todo el lifecycle del equipo docente: vista propia del docente, asignación masiva, clonado entre períodos, modificación de vigencia en bloque, y export a CSV. Siempre auditando `ASIGNACION_MODIFICAR`.

## What Changes

1. Nuevo router `app/routers/equipos.py` en `/api/equipos/*` con guard `equipos:asignar`.
2. Nuevo service `app/services/equipos.py` con lógica de:
   - `mis_equipos()` — filtrar Asignacion por user_id del JWT
   - `asignar_masiva()` — batch create de asignaciones en transacción
   - `clonar_equipo()` — duplicar asignaciones vigentes ajustando fechas
   - `modificar_vigencia()` — PUT bulk de desde/hasta
   - `exportar_equipo()` — generar CSV con cabeceras estándar
3. Nuevos schemas en `app/schemas/equipos.py`: `AsignacionMasivaRequest`, `ClonarRequest`, `ModificarVigenciaRequest`.
4. Audit `ASIGNACION_MODIFICAR` en cada operación mutante.

## Capabilities

### New Capabilities
- `equipos`: endpoints de gestión sobre Asignacion (masiva, clonar, vigencia, export, mis-equipos)

### Existing Capabilities
- `asignaciones`: se conserva `POST /api/asignaciones` individual (F4.1)

## Impact

### Affected Code
- `app/routers/equipos.py` — nuevo (5 endpoints)
- `app/services/equipos.py` — nuevo (5 métodos)
- `app/schemas/equipos.py` — nuevo (3 schemas request, responses)
- `app/main.py` — registrar router

### API Changes
- `GET /api/equipos/mis-equipos` — equipos del docente autenticado (F4.2)
- `GET /api/equipos` — gestión de asignaciones del tenant (F4.3)
- `POST /api/equipos/asignacion-masiva` — asignar docentes en bloque (F4.4)
- `POST /api/equipos/clonar` — clonar equipo entre cohortes (F4.5, RN-12)
- `PUT /api/equipos/vigencia` — modificar vigencia en bloque (F4.6)
- `GET /api/equipos/export` — exportar equipo a CSV (F4.7)

### Migration Required
- [ ] Database migration (no — Asignacion ya existe)
- [ ] API version bump (no — nuevo router)
- [ ] User communication needed (no)

## Risks

- [Risk] Clonado masivo (>500 asignaciones) puede exceder timeout → Mitigation: operación sincrónica con batch insert, monitorear. Si escala, migrar a worker.
- [Risk] CSV export con juego de caracteres → Mitigation: UTF-8 BOM para compatibilidad Excel.
