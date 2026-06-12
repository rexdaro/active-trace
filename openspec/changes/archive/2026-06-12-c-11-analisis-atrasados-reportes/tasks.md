# Tasks: C-11 — Análisis de Atrasados y Reportes

## Phase 1: Foundation

1. [ ] Agregar seed de permisos `atrasados:ver` y `atrasados:export` en `app/db/seed.py` con asignación a roles PROFESOR, TUTOR, COORDINADOR, ADMIN (atrasados:ver) y PROFESOR, COORDINADOR (atrasados:export).
2. [ ] Implementar `app/schemas/analisis.py` con esquemas Pydantic: `AlumnoAtrasado`, `AtrasadosResponse`, `RankingEntry`, `RankingResponse`, `ActividadReporte`, `ReporteMateria`, `EstadoSinDatos`, `NotaFinalAlumno`, `NotaFinalTextual`, `NotasFinalesResponse`, `MonitorAlumno`, `MonitorMateria`, `MonitorGeneralResponse`, `SeguimientoAlumno`, `SeguimientoResponse`.

## Phase 2: Repositorio — Nuevos Métodos de Agregación

3. [ ] Agregar método `get_all_by_materia(materia_id, tenant_id)` en `app/repositories/calificaciones.py` que retorna todas las calificaciones de una materia sin paginación, con eager load de la relación `EntradaPadron` para acceso a nombre, apellidos, comisión, regional.
4. [ ] Agregar método `get_actividades_by_materia(materia_id, tenant_id)` que retorna distinct `actividad` values para una materia.
5. [ ] Agregar método `get_entradas_with_calificaciones_by_materia(materia_id, tenant_id)` que retorna EntradaPadron entries que tienen al menos una calificación en la materia.

## Phase 3: Servicio de Análisis

6. [ ] Implementar helper `_resolve_scope(db, user, materia_id)` en `app/services/analisis.py` que:
    - Obtiene roles del usuario desde `user.user_roles`
    - Si tiene COORDINADOR o ADMIN → retorna scope "full"
    - Si tiene PROFESOR o TUTOR → busca asignación activa via `UmbralMateriaRepository.get_asignacion_id()` → si no existe, lanza 403; si existe, retorna scope "asignado"
7. [ ] Implementar `get_atrasados(db, materia_id, user)`:
    - Obtiene todas las calificaciones de la materia (vía repo)
    - Obtiene umbral (configurado o default)
    - Agrupa por entrada_padron_id
    - Detecta actividades del conjunto completo de la materia
    - Para cada alumno: identifica faltantes y desaprobadas según RN-06
    - Retorna lista de `AlumnoAtrasado` con motivo
8. [ ] Implementar `get_ranking(db, materia_id, user)`:
    - Obtiene calificaciones de la materia
    - Agrupa por entrada_padron_id, cuenta `aprobado = true`
    - Filtra donde count >= 1 (RN-09)
    - Ordena descendente por count, empates por apellidos
    - Asigna posición numérica
9. [ ] Implementar `get_reporte(db, materia_id, user)`:
    - Obtiene calificaciones de la materia
    - Calcula métricas globales: total_alumnos (distinct entrada_padron_id), total_actividades, total_calificaciones, aprobados, no_aprobados, porcentaje_aprobacion
    - Desglosa por actividad con métricas individuales
    - Si no hay datos, retorna `EstadoSinDatos`
10. [ ] Implementar `get_notas_finales(db, materia_id, user)`:
    - Obtiene calificaciones de la materia
    - Separa numéricas y textuales
    - Para numéricas: agrupa por alumno, calcula promedio simple
    - Para textuales: agrupa por alumno con lista de (actividad, nota_textual)
11. [ ] Implementar `export_tps_sin_corregir(db, materia_id, user)`:
    - Obtiene calificaciones de la materia
    - Detecta actividades textuales (RN-08) sin calificar por alumno (RN-07)
    - Genera CSV con columnas: Apellidos, Nombre, Email, Actividad, Comisión, Regional
    - Retorna `StreamingResponse` con headers de descarga
    - Registra audit `ANALISIS_CONSULTA` con tipo "export_tps_sin_corregir"
12. [ ] Implementar `get_monitor_general(db, user, filtros)`:
    - Valida que usuario sea COORDINADOR o ADMIN (403 si no)
    - Obtiene entradas del padrón activas del tenant
    - Para cada alumno: obtiene calificaciones en todas las materias
    - Aplica filtros opcionales (materia_id, regional, comision, q, estado_actividad)
    - Retorna vista paginada con métricas por materia
    - Registra audit `ANALISIS_CONSULTA` con tipo "monitor_general"
13. [ ] Implementar `get_monitor_seguimiento(db, user, filtros)`:
    - Resuelve scope del usuario
    - Obtiene calificaciones según scope
    - Aplica filtros opcionales (alumno_id, email, comision, regional, actividad, min_cumplimiento_pct)
    - Si COORDINADOR/ADMIN: aplica filtro adicional fecha_desde/fecha_hasta
    - Calcula pct_cumplimiento = aprobadas / total_actividades
    - Filtra por min_cumplimiento_pct si se especifica
    - Registra audit `ANALISIS_CONSULTA` con tipo "monitor_seguimiento"

## Phase 4: Routing

14. [ ] Implementar router `app/routers/analisis.py` con:
    - `GET /api/v1/analisis/materias/{materia_id}/atrasados` → `AnalisisService.get_atrasados()`
    - `GET /api/v1/analisis/materias/{materia_id}/ranking` → `AnalisisService.get_ranking()`
    - `GET /api/v1/analisis/materias/{materia_id}/reporte` → `AnalisisService.get_reporte()`
    - `GET /api/v1/analisis/materias/{materia_id}/notas-finales` → `AnalisisService.get_notas_finales()`
    - `GET /api/v1/analisis/materias/{materia_id}/tps-sin-corregir` → `AnalisisService.export_tps_sin_corregir()` (StreamingResponse)
    - `GET /api/v1/analisis/monitor/general` → `AnalisisService.get_monitor_general()` con guard condicional de rol
    - `GET /api/v1/analisis/monitor/seguimiento` → `AnalisisService.get_monitor_seguimiento()`
15. [ ] Registrar router en `app/main.py` con prefijo `/api/v1/analisis`.
16. [ ] Agregar guard `atrasados:ver` como dependency en todos los endpoints del router `analisis.py`.

## Phase 5: Quality & Documentation

17. [ ] Tests de atrasados (F2.2):
    - alumno con actividad faltante es detectado
    - alumno con nota bajo umbral es detectado
    - alumno con todas aprobadas no aparece
    - materia sin calificaciones retorna lista vacía
    - scope PROFESOR limita resultados
18. [ ] Tests de ranking (F2.3):
    - orden descendente por aprobados
    - empate ordenado alfabéticamente
    - alumno sin aprobadas excluido (RN-09)
    - paginación funciona correctamente
19. [ ] Tests de reporte rápido (F2.4):
    - métricas globales correctas
    - desglose por actividad
    - materia sin datos retorna estado informativo
20. [ ] Tests de notas finales (F2.5):
    - promedio simple de numéricas
    - notas textuales en sección separada
    - alumno sin calificaciones no aparece
21. [ ] Tests de export TPs sin corregir (F2.6):
    - CSV incluye solo textuales sin calificar (RN-07/08)
    - cabeceras correctas
    - todas calificadas → CSV solo con cabeceras
    - audit registrado
22. [ ] Tests de monitor general (F2.7):
    - ADMIN ve todos los alumnos
    - PROFESOR recibe 403
    - filtro por materia funciona
    - búsqueda libre funciona
    - audit registrado
23. [ ] Tests de monitor seguimiento (F2.8/F2.9):
    - PROFESOR ve solo asignados
    - COORDINADOR ve todos
    - filtro fecha solo disponible para COORDINADOR/ADMIN
    - filtro mínimo cumplimiento funciona
    - filtro por actividad funciona
    - audit registrado
24. [ ] Tests de scoping:
    - PROFESOR sin asignación activa recibe 403
    - TUTOR ve solo sus alumnos
    - ADMIN sin restricción

## Phase 6: Deployment

25. [ ] Ejecutar seed de permisos `atrasados:ver` y `atrasados:export` en entorno de staging.
26. [ ] Verificar los 7 endpoints con datos reales (calificaciones importadas vía C-10).
27. [ ] Validar scoping por rol: autenticarse como PROFESOR, TUTOR, COORDINADOR y ADMIN, verificar que cada uno ve los datos esperados.
28. [ ] Validar export CSV se descarga correctamente en Excel/Calc.
