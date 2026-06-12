# Proposal: C-10 — Calificaciones y Umbral

## Why

Activia-Trace necesita procesar calificaciones de alumnos para detectar atrasados, generar rankings y comunicar resultados. Hoy el sistema tiene padrón de alumnos (C-09) pero no existe modelo ni mecanismo para importar notas desde el LMS.

**Context**: El LMS exporta calificaciones en archivos de hoja de cálculo con una combinación de notas numéricas y textuales. El docente necesita importar esos datos, seleccionar qué actividades incluir y configurar su propio criterio de aprobación. Sin este módulo, el flujo central del PROFESOR (FL-02) no puede ejecutarse.

**Current state**: No hay modelo de calificaciones. No hay umbral de aprobación configurable. No hay forma de derivar `aprobado` a partir de notas.

**Desired state**: El sistema puede importar calificaciones desde archivo del LMS con detección automática de columnas numéricas (RN-01) y textuales (RN-02), vista previa y selección de actividades. El docente configura su umbral de aprobación por materia (defecto 60%, RN-03). El sistema deriva automáticamente el campo `aprobado`. Soporta reporte de finalización para detectar entregas sin corregir (RN-07/08). El vaciado de datos respeta scope aislado por usuario (RN-04).

## What Changes

1. Modelos `Calificacion` (numérica/textual, `aprobado` derivado, origen Importado/Manual) y `UmbralMateria` (umbral_pct por asignación, valores aprobatorios).
2. Import de calificaciones desde archivo LMS (F1.1): upload → detecta columnas numéricas (RN-01) y textuales (RN-02) → preview → selección de actividades → confirmación.
3. Import de reporte de finalización (F1.2): upload → cruce contra calificaciones → lista de "posibles sin corregir" (RN-07/08).
4. Configurar umbral por materia (F2.1, RN-03, defecto 60%) con scope por asignación docente.
5. Vaciado de datos scope-isolated (RN-04) auditado como `CALIFICACIONES_IMPORTAR`.
6. Migración Alembic con `calificacion` y `umbral_materia`.
7. Tests: derivación `aprobado` (numérica vs umbral, textual vs conjunto), import + preview, selección de actividades, umbral por asignación, vaciado scope-isolated.

## Capabilities

### New Capabilities
- `calificaciones`: modelo de notas con derivación automática de aprobación, import desde archivo LMS, preview y confirmación en dos pasos
- `umbral-materia`: configuración de umbral de aprobación por asignación docente con valores por defecto y aprobación textual

### Modified Capabilities
- `academic-structure`: nuevas relaciones Materia→Calificacion, Materia→UmbralMateria, EntradaPadron→Calificacion

## Impact

### Affected Specifications
- `openspec/specs/padron/spec.md` — nuevas relaciones EntradaPadron→Calificacion
- `openspec/specs/calificaciones/spec.md` — nuevo spec de dominio

### Affected Code
- `app/models/` — nuevos `calificacion.py`, `umbral_materia.py`
- `app/schemas/` — nuevos esquemas Pydantic para import, preview, umbral
- `app/services/` — nuevo servicio de calificaciones con lógica de derivación e import
- `app/repositories/` — nuevo repositorio de calificaciones y umbral
- `app/routers/` — nuevo router de calificaciones con endpoints de import, preview, confirm, umbral, finalización, vaciado

### API Changes
- `POST /api/materias/{materia_id}/calificaciones/preview` — subir archivo LMS, detectar actividades, preview
- `POST /api/materias/{materia_id}/calificaciones/confirm` — confirmar import con actividades seleccionadas
- `GET /api/materias/{materia_id}/calificaciones` — listar calificaciones de una materia
- `PUT /api/materias/{materia_id}/umbral` — configurar umbral
- `GET /api/materias/{materia_id}/umbral` — obtener umbral actual
- `POST /api/materias/{materia_id}/calificaciones/finalizacion/preview` — preview reporte finalización
- `POST /api/materias/{materia_id}/calificaciones/finalizacion/confirm` — confirmar reporte finalización
- `DELETE /api/materias/{materia_id}/calificaciones/datos` — vaciar datos (scope RN-04)

### Migration Required
- [x] Database migration (calificacion, umbral_materia)
- [ ] API version bump
- [ ] User communication needed
- [ ] Documentation updates

## Timeline Estimate

Medium (2–3 semanas). Dependencies: C-09 already done.

## Risks

- [Risk] Archivos LMS con formato variable entre distintos Moodle → Mitigation: detección flexible de columnas por patrón de encabezado (RN-01, RN-02); preview permite al usuario verificar antes de confirmar.
- [Risk] Umbral configurado por un docente afecta datos de otro en la misma materia → Mitigation: UmbralMateria tiene FK a Asignacion (scope por docente). Cada docente ve su propio umbral.
- [Risk] Volumen grande de calificaciones (>10k registros por materia) → Mitigation: confirm procesa en worker si supera umbral definido; preview es rápida (solo cabeceras + muestra).
