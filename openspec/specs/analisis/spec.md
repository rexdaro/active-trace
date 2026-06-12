# analisis Specification

## Purpose

Define la capa de análisis y reportes que consume datos de `Calificacion`, `EntradaPadron` y `UmbralMateria` para producir insights académicos. Todos los cálculos son in-memory sin nuevos modelos de BD. Provee detección de atrasados, rankings, reportes consolidados, notas finales, exportación CSV y monitores multi-alumno con scoping por rol.

## Requirements

### Requirement: Alumnos Atrasados por Materia (F2.2)

WHEN un usuario con permiso `atrasados:ver` solicita los alumnos atrasados de una materia,
the system SHALL detectar alumnos que tienen actividades faltantes o nota inferior al umbral (RN-06)
AND SHALL determinar el motivo del atraso: "actividad_faltante" o "nota_bajo_umbral"
AND SHALL incluir las actividades específicas que causan cada estado.

#### Scenario: Alumno con actividad faltante es atrasado
GIVEN una materia M1 con actividades "TP1", "TP2" en sus calificaciones
AND el alumno A tiene calificación en "TP1" pero no en "TP2"
WHEN se consulta `GET /api/v1/analisis/materias/M1/atrasados`
THEN el alumno A aparece en la lista con `motivo = "actividad_faltante"`
AND `actividades_faltantes = ["TP2"]`.

#### Scenario: Alumno con nota bajo umbral es atrasado
GIVEN un `UmbralMateria` con `umbral_pct = 60` para la materia M1
AND el alumno A tiene calificación en "TP1" con `nota_numerica = 45` y `aprobado = false`
WHEN se consulta atrasados de M1
THEN el alumno A aparece con `motivo = "nota_bajo_umbral"`
AND `actividades_desaprobadas = ["TP1"]`.

#### Scenario: Alumno con todas las actividades aprobadas no es atrasado
GIVEN el alumno A tiene calificaciones en todas las actividades de M1 con `aprobado = true`
WHEN se consulta atrasados de M1
THEN el alumno A NO aparece en la lista de atrasados.

#### Scenario: Atrasados para materia sin calificaciones
GIVEN la materia M1 no tiene ninguna calificación registrada
WHEN se consulta atrasados de M1
THEN el sistema retorna lista vacía con `total = 0`.

#### Scenario: Scope PROFESOR limita atrasados a su asignación
GIVEN un PROFESOR P1 con asignación activa en materia M1
AND otro PROFESOR P2 también con asignación en M1
WHEN P1 consulta atrasados de M1
THEN solo ve los alumnos asociados a la asignación de P1
AND no incluye datos de la asignación de P2.

---

### Requirement: Ranking de Actividades Aprobadas (F2.3)

WHEN un usuario con permiso `atrasados:ver` solicita el ranking de una materia,
the system SHALL ordenar los alumnos por cantidad de actividades aprobadas descendente
AND SHALL excluir alumnos sin ninguna actividad aprobada (RN-09)
AND SHALL incluir la posición numérica en el ranking.

#### Scenario: Ranking ordena por aprobados descendente
GIVEN alumno A tiene 3 actividades aprobadas, alumno B tiene 5, alumno C tiene 2
WHEN se consulta `GET /api/v1/analisis/materias/M1/ranking`
THEN el ranking es: B (posición 1), A (posición 2), C (posición 3).

#### Scenario: Empate en ranking se ordena alfabéticamente
GIVEN alumno A (apellidos "García") y alumno B (apellidos "Benítez") ambos con 3 aprobadas
WHEN se consulta el ranking
THEN B aparece antes que A en la misma posición de puntaje.

#### Scenario: Alumno sin actividades aprobadas no aparece (RN-09)
GIVEN alumno C tiene 0 actividades aprobadas en M1
WHEN se consulta el ranking
THEN alumno C NO aparece en la lista.

#### Scenario: Ranking paginado
GIVEN 100 alumnos con actividades aprobadas en M1
WHEN se consulta ranking con `limit=10, offset=0`
THEN el sistema retorna los primeros 10 alumnos
AND `total = 100`.

---

### Requirement: Reporte Rápido por Materia (F2.4)

WHEN un usuario con permiso `atrasados:ver` solicita el reporte rápido de una materia,
the system SHALL calcular métricas consolidadas: total_alumnos, total_actividades, total_calificaciones, aprobados, no_aprobados, porcentaje_aprobacion
AND SHALL desglosar métricas por actividad individual
AND SHALL retornar estado informativo cuando no hay datos.

#### Scenario: Reporte con datos calcula métricas correctamente
GIVEN materia M1 tiene 10 alumnos, 3 actividades, 30 calificaciones (20 aprobadas, 10 no aprobadas)
WHEN se consulta `GET /api/v1/analisis/materias/M1/reporte`
THEN `total_alumnos = 10`, `total_actividades = 3`, `total_calificaciones = 30`
AND `aprobados = 20`, `no_aprobados = 10`, `porcentaje_aprobacion = 66.67`
AND `por_actividad` contiene 3 entries con sus respectivas métricas.

#### Scenario: Reporte sin datos retorna estado informativo
GIVEN materia M1 no tiene calificaciones
WHEN se consulta el reporte
THEN el sistema retorna `{ "sin_datos": true, "mensaje": "No hay calificaciones para esta materia" }`.

#### Scenario: Reporte desglosa métricas por actividad
GIVEN materia M1 tiene actividad "TP1" con 10 calificaciones (7 aprobadas, 3 no)
AND actividad "TP2" con 10 calificaciones (5 aprobadas, 5 no)
WHEN se consulta el reporte
THEN `por_actividad` incluye entrada para "TP1" con 7 aprobados
AND entrada para "TP2" con 5 aprobados.

---

### Requirement: Notas Finales Agrupadas (F2.5)

WHEN un usuario con permiso `atrasados:ver` solicita las notas finales de una materia,
the system SHALL agrupar calificaciones por alumno
AND SHALL calcular el promedio simple de notas numéricas por alumno
AND SHALL agrupar alumnos con solo notas textuales en sección separada.

#### Scenario: Promedio simple de notas numéricas
GIVEN alumno A tiene notas 70, 80, 90 en actividades de M1
WHEN se consulta `GET /api/v1/analisis/materias/M1/notas-finales`
THEN `promedio = 80.0`
AND `actividades_count = 3`.

#### Scenario: Alumno con notas textuales en sección separada
GIVEN alumno A solo tiene calificaciones textuales ("Satisfactorio", "Supera lo esperado")
WHEN se consulta notas-finales
THEN alumno A aparece en `notas_textuales`
AND NO aparece en `notas_numericas`.

#### Scenario: Alumno sin calificaciones no aparece
GIVEN alumno A no tiene calificaciones en M1
WHEN se consulta notas-finales
THEN alumno A no aparece en ninguna sección.

---

### Requirement: Exportar TPs sin Corregir (F2.6)

WHEN un usuario con permiso `atrasados:ver` solicita la exportación de TPs sin corregir de una materia,
the system SHALL detectar actividades con nota nula (sin calificar) por alumno (RN-07)
AND SHALL incluir solo actividades textuales (RN-08)
AND SHALL retornar un archivo CSV descargable.

#### Scenario: CSV incluye actividades textuales sin calificar (RN-07/08)
GIVEN alumno A tiene actividad textual "TP Final" sin calificación en M1
AND actividad numérica "TP1 (Real)" sin calificación en M1
WHEN se consulta `GET /api/v1/analisis/materias/M1/tps-sin-corregir`
THEN el CSV incluye fila para (alumno A, "TP Final")
AND NO incluye fila para (alumno A, "TP1 (Real)") por ser numérica (RN-08).

#### Scenario: CSV tiene cabeceras correctas
GIVEN materia M1 con TPs sin corregir
WHEN se consulta el endpoint de exportación
THEN el archivo tiene `Content-Type: text/csv`
AND `Content-Disposition: attachment`
AND las columnas son: Apellidos, Nombre, Email, Actividad, Comisión, Regional.

#### Scenario: Sin TPs sin corregir retorna CSV vacío con cabeceras
GIVEN materia M1 tiene todas las actividades calificadas
WHEN se consulta el export
THEN el CSV contiene solo las cabeceras sin filas de datos.

---

### Requirement: Monitor General (F2.7)

WHEN un usuario COORDINADOR o ADMIN solicita el monitor general,
the system SHALL mostrar una vista transversal de todos los alumnos del tenant con estado de actividades en todas las materias
AND SHALL aplicar filtros opcionales: materia_id, regional, comisión, búsqueda libre, estado de actividad
AND SHALL retornar 403 si el usuario es PROFESOR o TUTOR.

#### Scenario: Monitor general incluye todas las materias del alumno
GIVEN alumno A tiene calificaciones en materias M1 y M2
WHEN se consulta `GET /api/v1/analisis/monitor/general`
THEN alumno A aparece con `materias` conteniendo entries para M1 y M2.

#### Scenario: Filtro por materia limita resultados
GIVEN alumno A tiene calificaciones en M1 y M2, alumno B solo en M1
WHEN se consulta monitor general con `materia_id=M1`
THEN ambos alumnos A y B aparecen
AND solo la materia M1 se incluye en cada alumno.

#### Scenario: Búsqueda libre por nombre
GIVEN alumno "Carlos García" y alumno "María López" en el tenant
WHEN se consulta monitor general con `q=García`
THEN solo "Carlos García" aparece en resultados.

#### Scenario: PROFESOR recibe 403 en monitor general
GIVEN un usuario con rol PROFESOR
WHEN intenta acceder a `GET /api/v1/analisis/monitor/general`
THEN el sistema retorna 403 Forbidden.

---

### Requirement: Monitor de Seguimiento (F2.8/F2.9)

WHEN un usuario solicita el monitor de seguimiento,
the system SHALL mostrar el estado de actividades de alumnos filtrable por alumno_id, email, comisión, regional, actividad y mínimo de cumplimiento
AND SHALL limitar el alcance según el rol: PROFESOR/TUTOR ven solo sus asignaciones (F2.8); COORDINADOR/ADMIN ven todo con filtro adicional de rango de fechas (F2.9).

#### Scenario: PROFESOR ve solo alumnos de su asignación (F2.8)
GIVEN PROFESOR P1 con asignación en comisión "A" de materia M1
AND alumno A1 en comisión "A" y alumno A2 en comisión "B"
WHEN se consulta `GET /api/v1/analisis/monitor/seguimiento`
THEN solo A1 aparece en los resultados.

#### Scenario: COORDINADOR ve todos los alumnos con filtro fechas (F2.9)
GIVEN COORDINADOR C1 consulta el monitor de seguimiento
WHEN se solicitan resultados con `fecha_desde=2026-01-01&fecha_hasta=2026-06-01`
THEN el sistema aplica el filtro de rango de fechas a las calificaciones consideradas.

#### Scenario: Filtro por mínimo cumplimiento
GIVEN alumno A tiene 3 de 5 actividades aprobadas (60%)
AND alumno B tiene 1 de 5 actividades aprobadas (20%)
WHEN se consulta seguimiento con `min_cumplimiento_pct=50`
THEN solo alumno A aparece (cumple >= 50%).

#### Scenario: Filtro por actividad específica
GIVEN alumno A tiene calificación en "TP1" y alumno B no tiene "TP1"
WHEN se consulta seguimiento con `actividad=TP1`
THEN solo alumno A aparece.

---

### Requirement: Auditoría de Consultas de Análisis

WHEN un usuario exporta TPs sin corregir o accede a monitores,
the system SHALL registrar un audit de tipo `ANALISIS_CONSULTA`
AND SHALL incluir materia_id, tipo de consulta y usuario.

#### Scenario: Audit al exportar TPs sin corregir
GIVEN un usuario exporta TPs sin corregir de materia M1
WHEN el sistema completa la exportación
THEN se registra `AuditLog` con `accion = "ANALISIS_CONSULTA"`
AND `detalle.tipo = "export_tps_sin_corregir"`.

#### Scenario: Audit al consultar monitor general
GIVEN un COORDINADOR consulta el monitor general
WHEN la consulta se completa exitosamente
THEN se registra `AuditLog` con `accion = "ANALISIS_CONSULTA"`
AND `detalle.tipo = "monitor_general"`.

---

### Requirement: Scoping por Rol en Análisis

WHEN un usuario autenticado accede a cualquier endpoint de análisis,
the system SHALL determinar el scope basado en sus roles
AND SHALL limitar los datos visibles según corresponda.

#### Scenario: PROFESOR sin asignación activa recibe 403
GIVEN un usuario con rol PROFESOR pero sin asignación activa en materia M1
WHEN intenta consultar atrasados de M1
THEN el sistema retorna 403 Forbidden.

#### Scenario: ADMIN ve todos los datos sin restricción
GIVEN un usuario con rol ADMIN
WHEN consulta cualquier endpoint de análisis de materia M1
THEN el sistema retorna datos de todos los alumnos del tenant en esa materia.

#### Scenario: TUTOR con asignación activa ve sus alumnos
GIVEN un usuario con rol TUTOR y asignación activa en materia M1
WHEN consulta atrasados de M1
THEN solo ve los alumnos asociados a su asignación.
