# padron Specification

## Purpose

Define el modelo versionado de alumnos por materia×cohorte y los mecanismos de ingesta (archivo manual y Moodle WS). Es la base de datos para las épicas de calificaciones, rankings y comunicaciones.

## ADDED Requirements

### Requirement: Versionado de Padrón

WHEN el sistema importa un nuevo padrón para una materia y cohorte,
the system SHALL crear una nueva `VersionPadron` con `activa = true`
AND desactivar cualquier `VersionPadron` previamente activa para el mismo par (materia, cohorte).

#### Scenario: Activar nueva versión desactiva la anterior
GIVEN una `VersionPadron` activa para (materia=X, cohorte=Y)
WHEN el sistema crea una nueva `VersionPadron` para (materia=X, cohorte=Y) con `activa = true`
THEN la versión anterior pasa a `activa = false`
AND la nueva versión es la única con `activa = true` para ese par.

#### Scenario: Nueva versión no afecta otras materias
GIVEN una versión activa para (materia=X, cohorte=Y)
WHEN el sistema crea una nueva versión para (materia=A, cohorte=B)
THEN la versión de (materia=X, cohorte=Y) permanece activa sin cambios.

---

### Requirement: Import de Padrón desde Archivo

WHEN un usuario con permiso `padron:importar` sube un archivo `.xlsx` o `.csv` con datos de alumnos,
the system SHALL generar una vista previa con las filas detectadas y las columnas mapeadas
AND SHALL requerir confirmación explícita antes de persistir.

#### Scenario: Preview exitoso con xlsx
GIVEN un archivo xlsx válido con columnas `nombre`, `apellidos`, `email`, `comision`, `regional`
WHEN el usuario sube el archivo a `POST /padron/preview`
THEN el sistema retorna un `preview_token` con las columnas detectadas y el conteo de filas
AND NO persiste ningún dato todavía.

#### Scenario: Preview exitoso con csv
GIVEN un archivo csv con delimitador coma o punto y coma y las mismas columnas
WHEN el usuario sube el archivo a `POST /padron/preview`
THEN el sistema detecta automáticamente el delimitador
AND retorna preview equivalente al formato xlsx.

#### Scenario: Confirmación de import
GIVEN un `preview_token` válido obtenido de un preview exitoso
WHEN el usuario confirma vía `POST /padron/confirm`
THEN el sistema crea la `VersionPadron` activa
AND desactiva la versión anterior (si existe)
AND inserta todas las entradas del padrón en `EntradaPadron`
AND registra un audit de tipo `PADRON_CARGAR`.

#### Scenario: Archivo con formato inválido
GIVEN un archivo que no es xlsx ni csv
WHEN el usuario intenta subirlo
THEN el sistema rechaza con error 400
AND el mensaje indica los formatos aceptados.

#### Scenario: Archivo vacío
GIVEN un archivo xlsx o csv sin filas de datos
WHEN el usuario lo sube
THEN el sistema retorna preview con 0 filas
AND el usuario puede decidir no confirmar.

---

### Requirement: EntradaSinUsuario

WHEN el sistema importa una entrada del padrón cuyo `email` no corresponde a ningún `Usuario` existente en el sistema,
the system SHALL crear la `EntradaPadron` con `usuario_id = NULL`.

#### Scenario: Alumno sin cuenta en el sistema
GIVEN un archivo de padrón con un email que no existe en la tabla `usuarios`
WHEN el sistema confirma el import
THEN la entrada se crea con `usuario_id = NULL`
AND el resto de los campos (nombre, apellidos, email, comision, regional) se registran normalmente.

#### Scenario: Alumno con cuenta existente
GIVEN un archivo de padrón con un email que sí existe en la tabla `usuarios`
WHEN el sistema confirma el import
THEN la entrada se crea con `usuario_id` apuntando al Usuario correspondiente.

---

### Requirement: Sincronización con Moodle WS

WHEN el sistema ejecuta una sincronización (nocturna o on-demand) con Moodle Web Services,
the system SHALL obtener el listado de participantes y actividades desde la API del LMS
AND SHALL crear/actualizar el padrón con los datos obtenidos
AND SHALL mapear errores de conexión a respuesta `502 Bad Gateway`.

#### Scenario: Sync on-demand exitosa
GIVEN un tenant con `moodle_ws_url` y `moodle_token` configurados
WHEN el usuario con permiso `padron:sincronizar` invoca `POST /padron/sync`
THEN el sistema consulta `get_participants()` y `get_activities()` para cada materia configurada
AND crea una `VersionPadron` con `origen = MoodleWS` para cada materia procesada.

#### Scenario: Sync con Moodle no disponible
GIVEN un tenant con Moodle WS configurado pero el servidor Moodle no responde
WHEN el sistema intenta sincronizar
THEN el sistema reintenta hasta 3 veces con backoff exponencial
AND si persiste el error, retorna `502 Bad Gateway`
AND NO modifica el padrón existente.

#### Scenario: Sync nocturna automática
WHEN el worker `sync_nightly` se ejecuta (diariamente a las 02:00 AM)
THEN recorre todas las materias con `moodle_ws_url` configurado
AND ejecuta sync para cada una
AND registra resultado en logs (éxito/error por materia).

---

### Requirement: Vaciado de Datos con Scope Aislado

WHEN un usuario con permiso `padron:vaciar` solicita vaciar los datos de padrón de una materia,
the system SHALL eliminar únicamente las versiones de padrón cargadas por ese usuario en esa materia
AND SHALL registrar un audit de tipo `PADRON_CARGAR`.

#### Scenario: Vaciar datos propios
GIVEN un usuario U1 que cargó 2 versiones de padrón para materia M1
WHEN U1 invoca `DELETE /padron/M1/datos`
THEN las 2 versiones de U1 en M1 se eliminan
AND las versiones de otros usuarios en M1 no se modifican.

#### Scenario: Vaciar datos de materia sin versiones propias
GIVEN un usuario U1 sin versiones de padrón en materia M1
WHEN U1 invoca `DELETE /padron/M1/datos`
THEN el sistema retorna éxito (no hay datos que eliminar)
AND No se registra audit.

---

### Requirement: Aislamiento Multi-tenant

WHEN el sistema ejecuta cualquier consulta sobre `VersionPadron` o `EntradaPadron`,
the system SHALL filtrar por `tenant_id` del usuario autenticado
AND SHALL garantizar que ningún query cruce datos entre tenants.

#### Scenario: Datos aislados por tenant
GIVEN tenant A con padrón cargado para materia M1 y tenant B sin datos
WHEN un usuario de tenant B consulta versiones de M1 (mismo UUID)
THEN el sistema retorna lista vacía.

#### Scenario: Inserción protege tenant_id
GIVEN un intento de insertar EntradaPadron con `tenant_id` distinto al del usuario autenticado
WHEN el repositorio recibe la solicitud
THEN el repositorio sobreescribe `tenant_id` con el del usuario autenticado antes de persistir.
