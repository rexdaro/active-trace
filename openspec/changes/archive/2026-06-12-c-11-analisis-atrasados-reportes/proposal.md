# Proposal: C-11 — Análisis de Atrasados y Reportes

## Why

Activia-Trace ya cuenta con calificaciones importadas (C-10) pero los docentes y coordinadores no tienen visibilidad del estado académico de los alumnos. No existe forma de responder preguntas fundamentales: ¿quiénes están atrasados? ¿cómo se rankean los alumnos por actividades aprobadas? ¿cuál es el panorama general por materia?

**Context**: C-10 proveyó el modelo de notas y umbral. Ahora necesitamos la capa de análisis que consume esos datos y produce insights sin crear nuevos modelos.

**Current state**: Calificaciones y umbral existen en BD pero no hay endpoints de consulta ni agregación. No hay forma de detectar atrasados, generar rankings, ni exportar reportes.

**Desired state**: Siete endpoints de análisis bajo `/api/v1/analisis` que exponen: lista de atrasados (F2.2), ranking de actividades aprobadas (F2.3), reporte rápido por materia (F2.4), notas finales agrupadas (F2.5), exportación de TPs sin corregir (F2.6), monitor general (F2.7) y monitor de seguimiento (F2.8/F2.9). Todo el cálculo es in-memory desde Calificacion + EntradaPadron + UmbralMateria. Sin nuevos modelos.

## What Changes

1. Servicio `AnalisisService` con lógica pura de cálculo: atrasados (RN-06), ranking (RN-09), reporte rápido, notas finales, detección de TPs sin corregir (RN-07/08), monitores general y de seguimiento.
2. Siete endpoints REST bajo prefix `/api/v1/analisis` con guard `atrasados:ver`.
3. Scoping por rol: PROFESOR/TUTOR ven solo alumnos de sus asignaciones; COORDINADOR/ADMIN ven todo el tenant.
4. Export CSV de TPs sin corregir como `StreamingResponse`.
5. Nuevos esquemas Pydantic para respuestas de análisis en `app/schemas/analisis.py`.
6. Tests para cada funcionalidad: atrasados, ranking, reporte, notas finales, export, monitores.

## Capabilities

### New Capabilities
- `analisis`: capa de análisis y reportes in-memory sobre calificaciones existentes. Incluye detección de atrasados, ranking, reporte rápido, notas finales, exportación y monitores.

### No Modified Capabilities
- C-10 (`calificaciones`): sin cambios, solo se consume como fuente de datos.

## Impact

### Affected Specifications
- `openspec/specs/calificaciones/spec.md` — nuevas relaciones de consumo desde analisis (no estructurales)

### Affected Code
- `app/services/` — nuevo `analisis.py`
- `app/schemas/` — nuevo `analisis.py`
- `app/routers/` — nuevo `analisis.py`
- `app/repositories/` — nuevos métodos de agregación en `calificaciones.py`

### New Permission Seed
- `atrasados:ver` — permiso para todos los endpoints de análisis
- `atrasados:export` — permiso para exportación CSV (opcional, puede unificarse con `ver`)

### API Changes
- `GET /api/v1/analisis/materias/{materia_id}/atrasados` — lista alumnos atrasados (F2.2)
- `GET /api/v1/analisis/materias/{materia_id}/ranking` — ranking de aprobados (F2.3)
- `GET /api/v1/analisis/materias/{materia_id}/reporte` — reporte rápido (F2.4)
- `GET /api/v1/analisis/materias/{materia_id}/notas-finales` — notas finales (F2.5)
- `GET /api/v1/analisis/materias/{materia_id}/tps-sin-corregir` — export CSV (F2.6)
- `GET /api/v1/analisis/monitor/general` — monitor general con filtros (F2.7)
- `GET /api/v1/analisis/monitor/seguimiento` — monitor seguimiento (F2.8/F2.9)

### Migration Required
- [x] Seed de permisos (`atrasados:ver`, `atrasados:export`)
- [ ] API version bump
- [ ] User communication needed
- [ ] Documentation updates

## Timeline Estimate

Medium (2–3 semanas). Dependencies: C-10 already done.

## Risks

- [Risk] Volumen grande de calificaciones (>10k registros por materia) puede hacer lentos los cálculos in-memory → Mitigation: paginación y límites en endpoints de lista; monitores con filtros obligatorios; considerar caché en futura iteración.
- [Risk] Scoping por asignación de PROFESOR depende de que la asignación exista → Mitigation: si no hay asignación activa, endpoint retorna 403 con mensaje claro.
- [Risk] Notas finales agrupadas no tienen fórmula definida (promedio simple, ponderado) → Mitigation: en v1 se implementa promedio simple de notas numéricas; se documenta como comportamiento base para futura configurabilidad.
