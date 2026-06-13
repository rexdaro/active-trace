## ADDED Requirements

### Requirement: Creación de ProgramaMateria
El sistema SHALL permitir crear un programa de materia con título y referencia de archivo, asociado a una materia, carrera y cohorte específicas.

#### Scenario: Creación exitosa
- **WHEN** un ADMIN o COORDINADOR envía un POST con materia_id, carrera_id, cohorte_id, titulo y referencia_archivo
- **THEN** el programa se registra con los datos provistos y un timestamp de carga (cargado_at)

#### Scenario: Creación con materia inexistente
- **WHEN** se envía un materia_id que no existe
- **THEN** el sistema retorna 404

### Requirement: Listado de programas
El sistema SHALL listar programas de materia filtrables por materia, carrera y cohorte.

#### Scenario: Listado sin filtros
- **WHEN** se consulta GET /api/v1/programas
- **THEN** se retorna la lista paginada de todos los programas del tenant

#### Scenario: Listado filtrado por materia
- **WHEN** se consulta GET /api/v1/programas?materia_id=<uuid>
- **THEN** se retornan solo los programas de esa materia

### Requirement: Obtención de programa
El sistema SHALL permitir obtener un programa específico por su ID.

#### Scenario: Obtención exitosa
- **WHEN** se consulta GET /api/v1/programas/{id} con un ID válido
- **THEN** se retorna el programa completo

#### Scenario: Programa no encontrado
- **WHEN** se consulta GET /api/v1/programas/{id} con un ID inexistente
- **THEN** el sistema retorna 404

### Requirement: Reemplazo de programa
El sistema SHALL permitir reemplazar (actualizar) un programa existente.

#### Scenario: Reemplazo exitoso
- **WHEN** se envía PUT /api/v1/programas/{id} con nuevos valores
- **THEN** el programa se actualiza con los nuevos datos

### Requirement: Eliminación de programa
El sistema SHALL permitir eliminar (soft-delete) un programa.

#### Scenario: Eliminación exitosa
- **WHEN** se envía DELETE /api/v1/programas/{id}
- **THEN** el programa se marca como eliminado (deleted_at seteado) y no aparece en listados

### Requirement: Aislamiento multi-tenant en programas
El sistema SHALL asegurar que un tenant solo acceda a sus propios programas.

#### Scenario: Programa de otro tenant no visible
- **WHEN** se consulta un programa de otro tenant
- **THEN** el sistema retorna 404

#### Scenario: Listado solo incluye programas del tenant actual
- **WHEN** se listan programas
- **THEN** solo se incluyen programas del tenant del usuario autenticado
