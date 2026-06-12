# Proposal: C-09 — Padrón Ingesta Moodle

## Why

Activia-Trace necesita datos de alumnos para funcionar: calificaciones, rankings, comunicaciones. Hoy no existe un mecanismo para cargar alumnado en el sistema. Sin padrón, no hay trazabilidad.

**Context**: El LMS (Moodle) es la fuente de verdad de participantes por materia. Algunos tenants exponen Web Services; otros no. Necesitamos ambos caminos (WS + carga manual) y que el modelo sea versionado para no perder histórico.

**Current state**: No hay modelo de padrón. No hay integración Moodle. No hay forma de saber qué alumnos pertenecen a qué materia×cohorte.

**Desired state**: El sistema puede importar el padrón de alumnos por materia×cohorte desde archivo (xlsx/csv) o desde Moodle WS, manteniendo versionado histórico, con una única versión activa por materia×cohorte. Los datos se sincronizan con Moodle on-demand y nocturnamente. El docente puede vaciar sus datos (scope aislado por RN-04).

## What Changes

1. Modelos `VersionPadron` + `EntradaPadron` con versionado (activar nueva desactiva la anterior).
2. Import de padrón: endpoint con preview (F1.3, F1.4), soporte xlsx + csv (fallback manual).
3. Integración Moodle WS en `integrations/moodle_ws.py`: sync usuarios/actividades, nocturna + on-demand; errores → 502 con reintento.
4. Acción "vaciar datos de materia" (F1.5, RN-04) auditada como `PADRON_CARGAR`.
5. Migración Alembic con `version_padron` y `entrada_padron`.
6. Tests de versionado, import formatos, entrada sin usuario_id, aislamiento tenant, mock Moodle WS + 502 fallback.

## Capabilities

### New Capabilities
- `padron`: modelo versionado de alumnos por materia×cohorte, import, preview, vaciado

### Modified Capabilities
- `academic-structure`: nuevas relaciones Materia→VersionPadron, Cohorte→VersionPadron

## Impact

### Affected Specifications
- `openspec/specs/academic-structure/spec.md` — nuevas relaciones y reglas de versión activa
- `openspec/specs/padron/spec.md` — nuevo spec de dominio

### Affected Code
- `app/models/` — nuevos `version_padron.py`, `entrada_padron.py`
- `app/schemas/` — nuevos esquemas Pydantic para import y preview
- `app/services/` — nuevo `padron.py` con lógica de versionado e import
- `app/repositories/` — nuevo `padron.py` con queries scoped por tenant
- `app/routers/` — nuevo `padron.py` con endpoints de import, preview, confirm, vaciar, sync
- `app/integrations/moodle_ws.py` — nuevo cliente Moodle WS
- `app/workers/` — nuevo worker de sync nocturna

### API Changes
- `POST /api/padron/preview` — subir archivo y obtener preview
- `POST /api/padron/confirm` — confirmar import y activar versión
- `POST /api/padron/{materia_id}/v2` — import directo v2 (sin preview)
- `DELETE /api/padron/{materia_id}/datos` — vaciar datos (scope usuario)
- `POST /api/padron/sync` — sync on-demand con Moodle
- `GET /api/padron/{materia_id}/versiones` — listar versiones de padrón

### Migration Required
- [x] Database migration (version_padron, entrada_padron)
- [ ] API version bump
- [ ] User communication needed
- [ ] Documentation updates

## Timeline Estimate

Medium (2–3 semanas). Dependencies: C-07 already done.

## Risks

- [Risk] Moodle WS no disponible en algunos tenants → Mitigation: fallback a archivo manual (xlsx/csv) como flujo primario alternativo.
- [Risk] Archivos xlsx grandes (>10k filas) → Mitigation: procesamiento en worker con chunking.
- [Risk] RN-04 (scope aislado) conflictúa con RN-05 (upsert destructivo por materia) → Mitigation: el vaciado borra SOLO datos del usuario; el versionado de padrón es por materia×cohorte, no por usuario.
