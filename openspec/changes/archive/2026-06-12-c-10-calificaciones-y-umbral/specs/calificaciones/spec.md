# calificaciones Specification

## Purpose

Define el modelo de calificaciones y umbral de aprobación, los mecanismos de importación desde archivos del LMS (calificaciones y reporte de finalización), la derivación automática del campo `aprobado`, y la configuración de umbral por asignación docente. Es la base de datos para las épicas de análisis de atrasados, rankings y comunicaciones (C-11, C-12).

## ADDED Requirements

### Requirement: Modelo de Calificaciones

WHEN el sistema registra una calificación para un alumno en una actividad evaluable,
the system SHALL almacenar la nota como numérica y/o textual
AND SHALL derivar el campo `aprobado` según las reglas de negocio
AND SHALL registrar el origen de la calificación (Importado | Manual).

#### Scenario: Crear calificación numérica
GIVEN un alumno con `entrada_padron_id` en una materia
WHEN el sistema importa una nota numérica (ej: 75) para la actividad "TP1 (Real)"
THEN se crea una `Calificacion` con `nota_numerica = 75`, `nota_textual = null`
AND `origen = Importado`
AND `aprobado` se deriva comparando 75 contra el umbral de la materia.

#### Scenario: Crear calificación textual
GIVEN un alumno con `entrada_padron_id` en una materia
WHEN el sistema importa una nota textual "Satisfactorio" para la actividad "TP1"
THEN se crea una `Calificacion` con `nota_textual = "Satisfactorio"`, `nota_numerica = null`
AND `origen = Importado`
AND `aprobado` se deriva evaluando "Satisfactorio" contra los `valores_aprobatorios` configurados.

#### Scenario: Calificación sin nota no es aprobado
GIVEN un alumno sin nota numérica ni textual para una actividad
WHEN el sistema procesa la importación
THEN la calificación no se crea (no hay dato que registrar)
AND el alumno figura como "sin entregar" para esa actividad.

---

### Requirement: Derivación de Aprobado

WHEN el sistema crea o actualiza una calificación,
the system SHALL derivar `aprobado` usando el umbral configurado para la asignación del docente
AND SHALL aplicar las siguientes reglas:
- Si existe `nota_numerica`: `aprobado = nota_numerica >= umbral_efectivo`
- Si solo existe `nota_textual`: `aprobado = nota_textual in valores_aprobatorios`
- Si ambas son nulas: `aprobado = false`

#### Scenario: Aprobado por nota numérica sobre umbral
GIVEN un `UmbralMateria` con `umbral_pct = 60` para la asignación del docente
WHEN se crea una calificación con `nota_numerica = 75`
THEN `aprobado = true`.

#### Scenario: No aprobado por nota numérica bajo umbral
GIVEN un `UmbralMateria` con `umbral_pct = 60`
WHEN se crea una calificación con `nota_numerica = 45`
THEN `aprobado = false`.

#### Scenario: Aprobado por valor textual aprobatorio
GIVEN un `UmbralMateria` con `valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]`
WHEN se crea una calificación con `nota_textual = "Supera lo esperado"`
THEN `aprobado = true`.

#### Scenario: No aprobado por valor textual no aprobatorio
GIVEN un `UmbralMateria` con `valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]`
WHEN se crea una calificación con `nota_textual = "No satisfactorio"`
THEN `aprobado = false`.

#### Scenario: Umbral por defecto cuando no hay configuración
GIVEN que no existe `UmbralMateria` para la asignación del docente
WHEN se crea una calificación con `nota_numerica = 60`
THEN se usa el umbral por defecto de 60%
AND `aprobado = true`.

#### Scenario: Umbral por defecto con nota bajo 60%
GIVEN que no existe `UmbralMateria` para la asignación del docente
WHEN se crea una calificación con `nota_numerica = 59`
THEN se usa el umbral por defecto de 60%
AND `aprobado = false`.

---

### Requirement: Importar Calificaciones desde Archivo LMS

WHEN un usuario con permiso `calificaciones:importar` sube un archivo de calificaciones del LMS,
the system SHALL detectar automáticamente las columnas de actividades
AND SHALL clasificar cada columna como numérica (RN-01) o textual (RN-02)
AND SHALL ofrecer una vista previa con las actividades detectadas
AND SHALL requerir selección de actividades y confirmación explícita antes de persistir.

#### Scenario: Preview detecta columnas numéricas por sufijo (Real)
GIVEN un archivo xlsx con columnas "TP1 (Real)", "TP2 (Real)", "Nombre", "Apellido"
WHEN el usuario sube el archivo a `POST /materias/{materia_id}/calificaciones/preview`
THEN el sistema detecta "TP1" y "TP2" como actividades numéricas
AND "Nombre" y "Apellido" no se incluyen como actividades.

#### Scenario: Preview detecta columnas textuales por valores conocidos
GIVEN un archivo con columna "TP Final" que contiene valores "Satisfactorio", "No satisfactorio"
WHEN el usuario sube el archivo a preview
THEN el sistema detecta "TP Final" como actividad textual
AND muestra los valores únicos detectados en la preview.

#### Scenario: Preview muestra actividades detectadas
GIVEN un archivo con 3 actividades numéricas y 2 textuales
WHEN el preview se genera exitosamente
THEN la respuesta incluye una lista de 5 actividades con su tipo (numerica|textual)
AND el usuario puede seleccionar un subconjunto para importar.

#### Scenario: Confirmación de import con actividades seleccionadas
GIVEN un `preview_token` válido y una lista de actividades seleccionadas ["TP1", "TP Final"]
WHEN el usuario confirma vía `POST /materias/{materia_id}/calificaciones/confirm`
THEN el sistema crea calificaciones solo para esas 2 actividades
AND deriva `aprobado` para cada una
AND registra un audit de tipo `CALIFICACIONES_IMPORTAR`.

#### Scenario: Archivo con formato inválido
GIVEN un archivo que no es xlsx ni csv
WHEN el usuario intenta subirlo a preview
THEN el sistema rechaza con error 400
AND el mensaje indica los formatos aceptados (.xlsx, .csv).

#### Scenario: Alumno del archivo no encontrado en padrón
GIVEN un archivo con un alumno cuyo email no existe en `EntradaPadron` de la materia
WHEN el sistema genera el preview
THEN el alumno aparece en `errores[]` como "no mapeado"
AND no se incluye en la preview de calificaciones.

---

### Requirement: Configurar Umbral por Materia

WHEN un usuario con permiso `calificaciones:importar` configura el umbral de una materia,
the system SHALL crear o actualizar el `UmbralMateria` asociado a su asignación docente
AND SHALL usar ese umbral como criterio de aprobación para futuras importaciones
AND SHALL retornar el umbral por defecto (60%) si no existe configuración.

#### Scenario: Configurar umbral personalizado
GIVEN un docente con asignación en materia M1
WHEN el docente envía `PUT /materias/M1/umbral` con `{ umbral_pct: 70, valores_aprobatorios: ["Satisfactorio", "Supera lo esperado", "Excelente"] }`
THEN se crea un `UmbralMateria` con esos valores para la asignación del docente
AND el sistema retorna el umbral creado.

#### Scenario: Actualizar umbral existente
GIVEN un `UmbralMateria` existente para la asignación con `umbral_pct = 70`
WHEN el docente envía `PUT /materias/M1/umbral` con `{ umbral_pct: 65 }`
THEN el umbral existente se actualiza a 65
AND los `valores_aprobatorios` se actualizan si se envían.

#### Scenario: Obtener umbral por defecto
GIVEN que no existe `UmbralMateria` para la asignación del docente en materia M1
WHEN el docente solicita `GET /materias/M1/umbral`
THEN el sistema retorna `{ umbral_pct: 60, valores_aprobatorios: ["Satisfactorio", "Supera lo esperado"], es_defecto: true }`.

#### Scenario: Umbral no afecta a otros docentes
GIVEN docente A con umbral 70% y docente B sin umbral configurado en la misma materia M1
WHEN cada docente importa calificaciones
THEN el docente A usa umbral 70%
AND el docente B usa umbral por defecto 60%.

---

### Requirement: Importar Reporte de Finalización

WHEN un usuario con permiso `calificaciones:importar` sube un reporte de finalización de actividades del LMS,
the system SHALL cruzar el reporte contra las calificaciones existentes
AND SHALL detectar actividades finalizadas por el alumno que aún no tienen calificación
AND SHALL filtrar únicamente actividades de tipo textual (RN-08).

#### Scenario: Detectar entregas sin calificar
GIVEN un reporte de finalización con actividad textual "TP Final" marcada como "Finalizado" para alumno A
AND NO existe calificación para (alumno A, actividad "TP Final")
WHEN el usuario sube el reporte a `POST /materias/{materia_id}/calificaciones/finalizacion/preview`
THEN el sistema incluye (alumno A, "TP Final") en `posibles_sin_corregir[]`.

#### Scenario: Actividades numéricas no se incluyen
GIVEN un reporte de finalización con actividad numérica "TP1 (Real)" marcada como "Finalizado" para alumno A
AND NO existe calificación para (alumno A, "TP1 (Real)")
WHEN el usuario sube el reporte
THEN la actividad "TP1 (Real)" NO aparece en `posibles_sin_corregir[]` (RN-08).

#### Scenario: Actividad ya calificada no aparece como sin corregir
GIVEN un reporte de finalización con actividad "TP Final" marcada como "Finalizado" para alumno A
AND ya existe una calificación para (alumno A, "TP Final")
WHEN el usuario sube el reporte
THEN el sistema NO incluye (alumno A, "TP Final") en `posibles_sin_corregir[]`.

#### Scenario: Confirmar reporte de finalización
GIVEN un `preview_token` válido de finalización con 5 posibles sin corregir
WHEN el usuario confirma vía `POST /materias/{materia_id}/calificaciones/finalizacion/confirm`
THEN el sistema confirma la detección
AND registra audit `CALIFICACIONES_IMPORTAR` con `detalle.tipo = "finalizacion"`.

---

### Requirement: Vaciado de Datos Scope-Isolated

WHEN un usuario con permiso `calificaciones:vaciar` solicita vaciar las calificaciones de una materia,
the system SHALL eliminar únicamente las calificaciones importadas por ese usuario en esa materia
AND SHALL registrar un audit de tipo `CALIFICACIONES_IMPORTAR`.

#### Scenario: Vaciar calificaciones propias
GIVEN un usuario U1 que importó calificaciones para materia M1
AND un usuario U2 que también importó calificaciones para M1
WHEN U1 invoca `DELETE /materias/M1/calificaciones/datos`
THEN las calificaciones de U1 en M1 se eliminan
AND las calificaciones de U2 en M1 no se modifican.

#### Scenario: Vaciar materia sin calificaciones propias
GIVEN un usuario U1 sin calificaciones importadas en materia M1
WHEN U1 invoca `DELETE /materias/M1/calificaciones/datos`
THEN el sistema retorna éxito con `eliminados_count = 0`
AND No se registra audit.

---

### Requirement: Aislamiento Multi-tenant

WHEN el sistema ejecuta cualquier consulta sobre `Calificacion` o `UmbralMateria`,
the system SHALL filtrar por `tenant_id` del usuario autenticado
AND SHALL garantizar que ningún query cruce datos entre tenants.

#### Scenario: Calificaciones aisladas por tenant
GIVEN tenant A con calificaciones para materia M1 y tenant B sin datos
WHEN un usuario de tenant B consulta calificaciones de M1 (mismo UUID)
THEN el sistema retorna lista vacía.

#### Scenario: Umbral aislado por tenant
GIVEN tenant A con umbral configurado en materia M1 y tenant B sin umbral
WHEN un usuario de tenant B solicita el umbral de M1
THEN el sistema retorna el umbral por defecto (no el de tenant A).

---

### Requirement: Auditoría de Importaciones

WHEN el sistema ejecuta una importación de calificaciones (preview+confirm) o un vaciado de datos,
the system SHALL registrar un audit de tipo `CALIFICACIONES_IMPORTAR`
AND SHALL incluir materia_id, filas_afectadas, y detalle según la operación.

#### Scenario: Audit al confirmar import
GIVEN una confirmación exitosa de import con 120 calificaciones
WHEN el sistema completa la operación
THEN se registra `AuditLog` con `accion = "CALIFICACIONES_IMPORTAR"`, `filas_afectadas = 120`
AND `detalle` incluye `tipo = "importacion"` y `actividades = ["TP1", "TP2"]`.

#### Scenario: Audit al vaciar datos
GIVEN un vaciado exitoso que elimina 50 calificaciones
WHEN el sistema completa la operación
THEN se registra `AuditLog` con `accion = "CALIFICACIONES_IMPORTAR"`, `filas_afectadas = 50`
AND `detalle` incluye `tipo = "vaciado"`.
