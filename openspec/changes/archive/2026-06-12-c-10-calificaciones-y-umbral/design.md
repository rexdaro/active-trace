# Design: C-10 — Calificaciones y Umbral

## Context

El flujo central del PROFESOR (FL-02) comienza con la importación de calificaciones desde el LMS. C-09 ya provee el padrón de alumnos; ahora necesitamos el modelo de notas, la detección automática de actividades, la configuración del criterio de aprobación y la detección de entregas sin corregir.

## Goals / Non-Goals

**Goals:**
- Modelo `Calificacion` con nota numérica y/o textual, campo `aprobado` derivado automáticamente.
- Modelo `UmbralMateria` configurable por asignación docente (defecto 60%).
- Import desde archivo LMS: detección de columnas numéricas (RN-01) y textuales (RN-02), preview en dos pasos, selección de actividades.
- Import de reporte de finalización: cruce contra calificaciones para detectar entregas sin corregir (RN-07/08).
- Vaciado scope-isolated por (usuario_id, materia_id) (RN-04).
- Auditoría de todas las operaciones con código `CALIFICACIONES_IMPORTAR`.
- Aislamiento multi-tenant en todas las queries.

**Non-Goals:**
- Cálculo de notas finales ni promedios ponderados (será en C-11).
- Integración directa con LMS vía API (solo import de archivos).
- Interfaz de usuario frontend (solo API).

## Architecture Overview

### Capas afectadas

```
routers/calificaciones.py        → POST /preview, /confirm, GET /, PUT /umbral, GET /umbral,
                                   POST /finalizacion/preview, /finalizacion/confirm,
                                   DELETE /datos
  └─ services/calificaciones.py  → Lógica de import, derivación aprobado, preview, confirm,
                                   finalización, vaciado
       ├─ repositories/calificaciones.py  → Queries scoped por tenant sobre Calificacion
       ├─ repositories/umbral_materia.py  → Queries scoped por tenant sobre UmbralMateria
       └─ services/audit.py              → AuditService.log_action("CALIFICACIONES_IMPORTAR")
```

### Flujo de Import de Calificaciones

1. Usuario sube archivo a `POST /materias/{materia_id}/calificaciones/preview`
2. `services.calificaciones.CalificacionesService.preview()` parsea el archivo:
   - Detecta columnas cuyo encabezado termina en `(Real)` → nota numérica (RN-01)
   - Detecta columnas textuales conocidas (RN-02): "Satisfactorio", "Supera lo esperado", "No satisfactorio", etc.
   - Mapea alumnos por `entrada_padron_id` usando email o nombre desde el archivo
   - Genera preview con actividades detectadas, filas mapeadas, errores de matching
3. Usuario revisa preview y selecciona qué actividades incluir vía `POST /confirm`
4. `services.calificaciones.CalificacionesService.confirm()`:
   - Crea `Calificacion` para cada (entrada_padron × actividad) seleccionada
   - Deriva `aprobado`: si `nota_numerica` existe → compara con umbral; si solo `nota_textual` existe → evalúa contra `valores_aprobatorios`
   - Registra audit `CALIFICACIONES_IMPORTAR` con filas_afectadas
5. Cada materia_id + archivo genera un lote; el preview_token es efímero (en memoria/cache)

### Flujo de Import de Finalización

1. Usuario sube reporte de finalización a `POST /materias/{materia_id}/calificaciones/finalizacion/preview`
2. El servicio parsea el archivo y cruza contra `Calificacion` existentes:
   - Detecta actividades marcadas como "finalizadas" en el reporte que NO tienen calificación en el sistema
   - Filtra solo actividades textuales (RN-08)
   - Genera preview de "posibles sin corregir"
3. Usuario confirma vía `POST .../finalizacion/confirm` → se persiste el reporte (opcional) y queda registrada la detección

### Flujo de Umbral

1. `GET /materias/{materia_id}/umbral` → retorna el `UmbralMateria` de la asignación del usuario autenticado, o el defecto (60%) si no existe
2. `PUT /materias/{materia_id}/umbral` → crea o actualiza `UmbralMateria` para la asignación del usuario

### Derivación de `aprobado`

La derivación ocurre en el momento de inserción/confirmación y se almacena como campo materializado en la tabla:

```
if nota_numerica is not None:
    aprobado = nota_numerica >= umbral_efectivo
elif nota_textual is not None:
    aprobado = nota_textual in valores_aprobatorios
else:
    aprobado = False  # sin nota no puede estar aprobado
```

El `umbral_efectivo` se resuelve como: `UmbralMateria.umbral_pct` si existe para la asignación, o 60% por defecto.

## Data Model

### Calificacion

```yaml
Table: calificaciones
  id                : UUID PK
  tenant_id         : UUID FK → Tenant
  entrada_padron_id : UUID FK → EntradaPadron
  materia_id        : UUID FK → Materia
  actividad         : str         # nombre de la actividad evaluable
  nota_numerica     : decimal     nullable (nulo si es textual)
  nota_textual      : str         nullable (descripción cualitativa)
  aprobado          : bool        DERIVADO (ver reglas de derivación)
  origen            : enum        Importado | Manual
  importado_at      : datetime
```

### UmbralMateria

```yaml
Table: umbrales_materia
  id                  : UUID PK
  tenant_id           : UUID FK → Tenant
  asignacion_id       : UUID FK → Asignacion
  materia_id          : UUID FK → Materia
  umbral_pct          : int         mínimo para aprobar (defecto: 60)
  valores_aprobatorios: list[str]   valores textuales que cuentan como aprobado
```

### Constraints
- Unique index `(tenant_id, entrada_padron_id, actividad, materia_id)` para evitar duplicados por actividad-alumno
- Unique index `(tenant_id, asignacion_id, materia_id)` en UmbralMateria (solo un umbral por asignación en una materia)
- FK de UmbralMateria → Asignacion con CASCADE delete
- FK de Calificacion → EntradaPadron con RESTRICT (no eliminar entrada con calificaciones)
- Tenant isolation via `tenant_id` en todas las tablas

## API Design

### POST /api/v1/materias/{materia_id}/calificaciones/preview
- **Request**: multipart/form-data con archivo xlsx/csv
- **Response**: `{ preview_token, actividades_detectadas[], alumnos_count, errores[] }`
- **Description**: cada actividad detectada incluye nombre, tipo (numerica|textual), valores_muestra
- **Permission**: `calificaciones:importar`

### POST /api/v1/materias/{materia_id}/calificaciones/confirm
- **Request**: `{ preview_token, actividades_seleccionadas: string[] }`
- **Response**: `{ calificaciones_count, aprobados_count, no_aprobados_count }`
- **Effect**: inserta Calificacion para cada (entrada_padron × actividad), deriva aprobado, audita
- **Permission**: `calificaciones:importar`

### GET /api/v1/materias/{materia_id}/calificaciones
- **Query params**: `entrada_padron_id` (opcional, filtra por alumno), `actividad` (opcional), `aprobado` (opcional)
- **Response**: lista paginada de Calificacion con datos del alumno desnormalizados
- **Permission**: `calificaciones:ver`

### PUT /api/v1/materias/{materia_id}/umbral
- **Request**: `{ umbral_pct: int, valores_aprobatorios: string[] }`
- **Response**: `{ umbral_materia }`
- **Effect**: crea o actualiza UmbralMateria para la asignación del usuario autenticado
- **Permission**: `calificaciones:importar`

### GET /api/v1/materias/{materia_id}/umbral
- **Response**: `{ umbral_pct, valores_aprobatorios, es_defecto: bool }`
- **Permission**: `calificaciones:ver`

### POST /api/v1/materias/{materia_id}/calificaciones/finalizacion/preview
- **Request**: multipart/form-data con archivo xlsx/csv
- **Response**: `{ preview_token, posibles_sin_corregir[] }` — cada item: alumno, actividad, fecha_entrega
- **Permission**: `calificaciones:importar`

### POST /api/v1/materias/{materia_id}/calificaciones/finalizacion/confirm
- **Request**: `{ preview_token }`
- **Response**: `{ registros_detectados: int }`
- **Permission**: `calificaciones:importar`

### DELETE /api/v1/materias/{materia_id}/calificaciones/datos
- **Effect**: elimina SOLO calificaciones importadas por el usuario autenticado en esa materia (scope RN-04)
- **Response**: `{ eliminados_count }`
- **Audit**: registra `CALIFICACIONES_IMPORTAR` con detalle de la acción
- **Permission**: `calificaciones:vaciar`

## Decisions

| Decisión | Opción | Razón |
|----------|--------|-------|
| `aprobado` materializado vs derivado en query | Materializado en inserción | Evita recalcular en cada query de ranking/reporte; simplifica queries de C-11 |
| Umbral por asignación docente | FK a Asignacion en UmbralMateria | Cada docente ve/configura su propio umbral sin afectar a otros en la misma materia |
| Preview token efímero | En memoria/cache (Redis o diccionario en app) | Evita re-procesar el archivo; el cliente confirma explícitamente |
| Detección de columnas por patrón de encabezado | Regex `\(Real\)$` para numéricas | Sigue RN-01; las textuales se detectan por valores conocidos (RN-02) |
| Finalización no crea calificaciones | Solo detecta ausencias | El reporte de finalización identifica "posibles sin corregir"; la calificación real se importa por separado |
| CASCADE en UmbralMateria→Asignacion | ON DELETE CASCADE | Si se elimina una asignación, el umbral asociado se limpia automáticamente |

## Risks / Trade-offs

- [Risk] Preview token en memoria se pierde si la app se reinicia → Mitigation: token con TTL corto (15 min); si expira, usuario debe re-subir el archivo
- [Risk] Matching de alumnos por email puede fallar si el LMS usa formato distinto → Mitigation: preview muestra alumnos no mapeados para que el usuario verifique
- [Risk] Umbral por defecto hardcodeado (60%) vs configurable por tenant → Mitigation: en v1 es constante; en futura iteración se puede agregar configuración por tenant
- [Risk] Archivos con muchas actividades (>50 columnas) → Mitigation: preview limitado a N actividades; el usuario selecciona un subconjunto

## Migration Plan

1. Crear migración Alembic con tablas `calificacion` y `umbral_materia`
2. Agregar índices únicos para (tenant_id, entrada_padron_id, actividad, materia_id)
3. Agregar índice único para (tenant_id, asignacion_id, materia_id) en UmbralMateria

## Open Questions

- ¿Debemos soportar recalcular `aprobado` cuando cambia el umbral? → En v1 no; el umbral nuevo aplica a futuras importaciones. Recalcular existentes sería una operación costosa que se aborda en C-11 si es necesario.
- ¿El reporte de finalización debe persistirse como modelo propio? → En v1 no; solo se cruza en memoria. Si se necesita histórico, se agrega modelo en iteración posterior.
