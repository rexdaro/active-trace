# Design: C-11 — Análisis de Atrasados y Reportes

## Context

C-10 proveyó el modelo `Calificacion` con notas numéricas/textuales, el campo `aprobado` derivado y `UmbralMateria` configurable por asignación docente. Ahora necesitamos la capa de análisis que consume esos datos para producir insights académicos: detección de atrasados, rankings, reportes consolidados y monitores multi-alumno.

**Principio rector**: No se crean nuevos modelos de BD. Todo el cálculo es in-memory en Python a partir de datos obtenidos vía repositorios existentes.

## Goals / Non-Goals

**Goals:**
- Detección de alumnos atrasados por materia (RN-06): actividades faltantes O nota < umbral.
- Ranking de alumnos por cantidad de actividades aprobadas (RN-09).
- Reporte rápido con métricas consolidadas por materia.
- Notas finales agrupadas (promedio simple de notas numéricas).
- Export CSV de TPs sin corregir (RN-07/08).
- Monitor general (F2.7) transversal a materias para COORDINADOR/ADMIN.
- Monitor de seguimiento scoped (F2.8) para PROFESOR/TUTOR y extendido (F2.9) para COORDINADOR/ADMIN.
- Scoping por rol: PROFESOR/TUTOR limitados a sus asignaciones; COORDINADOR/ADMIN sin restricción.
- Auditoría de consultas de exportación con `ANALISIS_CONSULTA`.

**Non-Goals:**
- Cálculo de notas ponderadas o con fórmula configurable (v1 usa promedio simple).
- Caché de resultados de análisis (se aborda en iteración posterior si hay problemas de performance).
- Interfaz de usuario frontend (solo API).
- Notificaciones a alumnos atrasados (será en C-12).

## Architecture Overview

### Capas afectadas

```
routers/analisis.py                → GET /materias/{materia_id}/atrasados,
                                      GET /materias/{materia_id}/ranking,
                                      GET /materias/{materia_id}/reporte,
                                      GET /materias/{materia_id}/notas-finales,
                                      GET /materias/{materia_id}/tps-sin-corregir,
                                      GET /monitor/general,
                                      GET /monitor/seguimiento
  └─ services/analisis.py          → Lógica de cálculo in-memory:
                                       get_atrasados, get_ranking, get_reporte,
                                       get_notas_finales, export_tps_sin_corregir,
                                       get_monitor_general, get_monitor_seguimiento
       ├─ repositories/calificaciones.py  → get_all_by_materia() con eager load de alumno
       ├─ repositories/padron.py          → get_entradas_by_materia()
       ├─ services/analisis.py            → helper para scope (asignaciones activas)
       └─ services/audit.py               → AuditService.log_action("ANALISIS_CONSULTA")
```

### Scoping por rol

La resolución de scope ocurre al inicio de cada operación:

1. Obtener roles del usuario autenticado desde `user.user_roles`
2. Si el usuario tiene rol COORDINADOR o ADMIN → scope irrestricto (todo el tenant)
3. Si el usuario tiene rol PROFESOR o TUTOR → obtener sus `Asignacion` activas para la materia vía `UmbralMateriaRepository.get_asignacion_id()` (base: user_id + contexto_id = materia_id)
4. Si no tiene asignación activa en la materia → 403 Forbidden

### Flujo de Atrasados (F2.2)

1. Resolver scope del usuario (asignación activa o no)
2. Obtener todas las `Calificacion` de la materia via `CalificacionesRepository.get_all_by_materia()` con eager load de `EntradaPadron`
3. Obtener `UmbralMateria` para la asignación del usuario (o default)
4. Agrupar calificaciones por `entrada_padron_id`
5. Determinar el conjunto de actividades de la materia (distinct `actividad`)
6. Para cada alumno:
   - Si falta alguna actividad del conjunto → `motivo = "actividad_faltante"`
   - Si todas las actividades existen pero alguna tiene `aprobado = false` → `motivo = "nota_bajo_umbral"`
   - Si todas están aprobadas → no atrasado
7. Retornar lista de alumnos atrasados con nombre, apellidos, comisión, actividades faltantes, actividades desaprobadas

### Flujo de Ranking (F2.3)

1. Obtener calificaciones de la materia con eager load de alumno
2. Agrupar por `entrada_padron_id`
3. Para cada alumno: contar `aprobado = true`
4. Filtrar donde count >= 1 (RN-09)
5. Orden descendente por count
6. En caso de empate: orden alfabético por apellidos

### Flujo de Reporte Rápido (F2.4)

1. Obtener calificaciones de la materia
2. Calcular métricas:
   - `total_alumnos`: distinct entrada_padron_id
   - `total_actividades`: distinct actividad
   - `total_calificaciones`: count
   - `aprobados`: count donde aprobado = true
   - `no_aprobados`: count donde aprobado = false
   - `porcentaje_aprobacion`: (aprobados / total_calificaciones) * 100
3. Calcular por actividad: nombre, count, aprobados, no_aprobados, porcentaje
4. Si no hay datos: retornar estado informativo `{ "sin_datos": true, "mensaje": "No hay calificaciones para esta materia" }`

### Flujo de Notas Finales (F2.5)

1. Obtener calificaciones de la materia (solo numéricas para el promedio)
2. Agrupar por `entrada_padron_id`
3. Para cada alumno con al menos una nota numérica:
   - Calcular promedio de `nota_numerica` de todas sus actividades
   - Incluir nombre, apellidos, comisión, promedio, cantidad de actividades consideradas
4. Alumnos con solo notas textuales se agrupan en sección separada

### Flujo de Export TPs sin corregir (F2.6)

1. Obtener todas las calificaciones de la materia
2. Obtener todas las `EntradaPadron` con calificaciones en la materia
3. Para cada alumno, detectar actividades con `nota_numerica IS NULL AND nota_textual IS NULL` (RN-07/08: sin calificar)
4. Generar CSV con columnas: Apellidos, Nombre, Email, Actividad, Comisión
5. Retornar `StreamingResponse` con `Content-Disposition: attachment; filename="tps-sin-corregir-{materia_id}.csv"`

### Flujo de Monitor General (F2.7)

1. Scope: solo COORDINADOR/ADMIN (si no → 403)
2. Obtener todas las entradas del padrón activas para el tenant
3. Para cada alumno, obtener TODAS sus calificaciones en TODAS las materias
4. Aplicar filtros opcionales: materia_id, regional, comisión, búsqueda libre (nombre/email), estado de actividad (aprobado/no_aprobado/faltante)
5. Armar vista con: alumno, materia, actividades totales, aprobadas, no aprobadas, faltantes

### Flujo de Monitor Seguimiento (F2.8/F2.9)

1. Si PROFESOR/TUTOR: scope por asignaciones activas del usuario (F2.8)
2. Si COORDINADOR/ADMIN: scope irrestricto + filtro adicional de rango de fechas (F2.9)
3. Filtros: alumno_id, email, comisión, regional, actividad, mínimo de actividades cumplidas (pct)
4. Para cada alumno en scope: calcular actividades totales, aprobadas, cumplimiento pct
5. Filtrar donde cumplimiento pct >= mínimo especificado (o mostrar todos por defecto)

## Data Model

No se crean nuevos modelos. Las estructuras existentes son:

### Calificacion (C-10)
```
id, tenant_id, entrada_padron_id, materia_id, actividad,
nota_numerica, nota_textual, aprobado, origen, importado_por, importado_at
```

### EntradaPadron (C-09)
```
id, tenant_id, version_id, usuario_id, nombre, apellidos, email (encrypted),
comision, regional
```

### UmbralMateria (C-10)
```
id, tenant_id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios
```

### Asignacion (C-07)
```
id, tenant_id, user_id, role_id, contexto_id, responsable_id, desde, hasta
```

## API Design

Prefix: `/api/v1/analisis`
Guard: `atrasados:ver` (todos los endpoints)

### GET /api/v1/analisis/materias/{materia_id}/atrasados
- **Response**: `{ atrasados: AlumnoAtrasado[], total: int }`
- **AlumnoAtrasado**: `{ entrada_padron_id, nombre, apellidos, comision, regional, actividades_faltantes: string[], actividades_desaprobadas: string[], motivo: "actividad_faltante" | "nota_bajo_umbral" }`
- **Permission**: `atrasados:ver`
- **Scope**: PROFESOR/TUTOR → solo su asignación; COORDINADOR/ADMIN → todos

### GET /api/v1/analisis/materias/{materia_id}/ranking
- **Query params**: `limit=50` (default), `offset=0`
- **Response**: `{ ranking: RankingEntry[], total: int }`
- **RankingEntry**: `{ posicion, entrada_padron_id, nombre, apellidos, comision, actividades_aprobadas: int, total_actividades: int }`
- **Permission**: `atrasados:ver`

### GET /api/v1/analisis/materias/{materia_id}/reporte
- **Response**: `ReporteMateria | EstadoSinDatos`
- **ReporteMateria**: `{ sin_datos: false, total_alumnos, total_actividades, total_calificaciones, aprobados, no_aprobados, porcentaje_aprobacion, por_actividad: ActividadReporte[] }`
- **EstadoSinDatos**: `{ sin_datos: true, mensaje: string }`
- **Permission**: `atrasados:ver`

### GET /api/v1/analisis/materias/{materia_id}/notas-finales
- **Query params**: `ordenar_por=promedio|apellidos`, `orden=asc|desc`
- **Response**: `{ notas_numericas: NotaFinalAlumno[], notas_textuales: NotaFinalTextual[] }`
- **NotaFinalAlumno**: `{ entrada_padron_id, nombre, apellidos, comision, promedio: Decimal, actividades_count: int }`
- **NotaFinalTextual**: `{ entrada_padron_id, nombre, apellidos, comision, actividades: { actividad: string, nota_textual: string }[] }`
- **Permission**: `atrasados:ver`

### GET /api/v1/analisis/materias/{materia_id}/tps-sin-corregir
- **Response**: CSV file (StreamingResponse)
- **Headers**: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="tps-sin-corregir-{materia_id}.csv"`
- **Permission**: `atrasados:ver`
- **Columns**: Apellidos, Nombre, Email, Actividad, Comisión, Regional

### GET /api/v1/analisis/monitor/general
- **Query params**: `materia_id` (opcional), `regional` (opcional), `comision` (opcional), `q` (búsqueda libre), `estado_actividad` (aprobado|no_aprobado|faltante, opcional), `offset=0`, `limit=50`
- **Response**: `{ alumnos: MonitorAlumno[], total: int, filtros_aplicados: dict }`
- **MonitorAlumno**: `{ entrada_padron_id, nombre, apellidos, email, comision, regional, materias: MonitorMateria[] }`
- **MonitorMateria**: `{ materia_id, materia_nombre, total_actividades, aprobadas, no_aprobadas, faltantes }`
- **Permission**: `atrasados:ver`
- **Scope**: solo COORDINADOR/ADMIN (403 si PROFESOR/TUTOR)

### GET /api/v1/analisis/monitor/seguimiento
- **Query params**: `alumno_id` (opcional), `email` (opcional), `comision` (opcional), `regional` (opcional), `actividad` (opcional), `min_cumplimiento_pct` (int, default 0), `fecha_desde` (opcional, solo COORDINADOR/ADMIN), `fecha_hasta` (opcional, solo COORDINADOR/ADMIN), `offset=0`, `limit=50`
- **Response**: `{ alumnos: SeguimientoAlumno[], total: int }`
- **SeguimientoAlumno**: `{ entrada_padron_id, nombre, apellidos, email, comision, regional, actividades_totales, aprobadas, no_aprobadas, faltantes, pct_cumplimiento: float }`
- **Permission**: `atrasados:ver`
- **Scope**: PROFESOR/TUTOR → solo sus asignaciones (F2.8); COORDINADOR/ADMIN → todo + filtro fechas (F2.9)

## Decisions

| Decisión | Opción | Razón |
|----------|--------|-------|
| Cálculo in-memory vs SQL agregaciones | In-memory en Python | Evita SQL complejo; los datasets por materia suelen ser pequeños (<10k registros); permite lógica condicional compleja (RN-06, RN-09) |
| Modelo de scope | Rol del user + Asignacion activa | Reutiliza Asignacion existente; no requiere nuevo modelo ni relación |
| Promedio simple para notas finales | Promedio de todas las numéricas | Simple, predecible; se puede hacer configurable en futura iteración |
| CSV export vs JSON download | StreamingResponse con CSV | Formato esperado por docentes para trabajar en Excel/Calc; es exportable directamente |
| Monitor general separado de seguimiento | Dos endpoints distintos | Diferentes filtros, diferentes scopes, diferentes audiencias (coordinación vs tutoría) |
| Estado sin datos como respuesta | Objeto con `sin_datos: true` | Evita errores 404 cuando la materia no tiene calificaciones; frontend puede mostrar estado informativo |
| Monitores con offset/limit paginación | Paginación estándar | Evita timeouts con muchos alumnos; frontend puede cargar progresivamente |

## Risks / Trade-offs

- [Risk] Cálculo in-memory puede ser lento con >50k calificaciones en una materia → Mitigation: monitores requieren al menos un filtro; ranking y atrasados tienen paginación; se agrega logging de duración para identificar cuellos de botella
- [Risk] Alumno sin actividades en la materia no aparece en ningún cálculo → Mitigation: atrasados solo considera alumnos que existen en el padrón y tienen al menos una actividad registrada en la materia (el padrón define la población)
- [Risk] Las notas textuales no tienen promedio → Mitigation: se separan en sección aparte en notas finales; no se incluyen en ranking
- [Risk] Scoping por asignación asume que la Asignacion tiene contexto_id = materia_id → Mitigation: misma convención usada en C-10 para UmbralMateria; consistente con el modelo existente

## Open Questions

- ¿El monitor general debe incluir materias sin calificaciones? → En v1 no; solo materias donde exista al menos una calificación para el alumno.
- ¿El CSV de TPs sin corregir debe incluir fecha de entrega? → En v1 no tenemos ese dato (C-10 no persiste reporte de finalización). Se deja columna vacía para futura iteración.
