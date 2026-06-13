## ADDED Requirements

### Requirement: Creación de FechaAcademica
El sistema SHALL permitir crear una fecha académica con tipo (Parcial, TP, Coloquio, Recuperatorio), número de instancia, período, fecha y título, asociada a una materia y cohorte.

#### Scenario: Creación exitosa
- **WHEN** un ADMIN o COORDINADOR envía un POST con materia_id, cohorte_id, tipo, numero, periodo, fecha y titulo
- **THEN** la fecha académica se registra con los datos provistos

#### Scenario: Creación con materia inexistente
- **WHEN** se envía un materia_id que no existe
- **THEN** el sistema retorna 404

#### Scenario: Creación con cohorte inexistente
- **WHEN** se envía un cohorte_id que no existe
- **THEN** el sistema retorna 404

### Requirement: Listado de fechas académicas
El sistema SHALL listar fechas académicas filtrables por materia, cohorte y tipo.

#### Scenario: Listado sin filtros
- **WHEN** se consulta GET /api/v1/fechas-academicas
- **THEN** se retorna la lista paginada de todas las fechas del tenant

#### Scenario: Listado filtrado por materia y cohorte
- **WHEN** se consulta GET /api/v1/fechas-academicas?materia_id=<uuid>&cohorte_id=<uuid>
- **THEN** se retornan solo las fechas de esa materia y cohorte

#### Scenario: Listado filtrado por tipo
- **WHEN** se consulta GET /api/v1/fechas-academicas?tipo=Parcial
- **THEN** se retornan solo las fechas de tipo Parcial

### Requirement: Obtención de fecha académica
El sistema SHALL permitir obtener una fecha académica específica por su ID.

#### Scenario: Obtención exitosa
- **WHEN** se consulta GET /api/v1/fechas-academicas/{id} con un ID válido
- **THEN** se retorna la fecha académica completa

#### Scenario: Fecha no encontrada
- **WHEN** se consulta GET /api/v1/fechas-academicas/{id} con un ID inexistente
- **THEN** el sistema retorna 404

### Requirement: Actualización de fecha académica
El sistema SHALL permitir actualizar una fecha académica existente.

#### Scenario: Actualización exitosa
- **WHEN** se envía PUT /api/v1/fechas-academicas/{id} con nuevos valores
- **THEN** la fecha académica se actualiza con los nuevos datos

### Requirement: Eliminación de fecha académica
El sistema SHALL permitir eliminar (soft-delete) una fecha académica.

#### Scenario: Eliminación exitosa
- **WHEN** se envía DELETE /api/v1/fechas-academicas/{id}
- **THEN** la fecha se marca como eliminada (deleted_at seteado) y no aparece en listados

### Requirement: Fragmento HTML embebible
El sistema SHALL generar un fragmento HTML con las fechas académicas de una materia×cohorte, apto para incrustar en un LMS.

#### Scenario: Generación de fragmento HTML
- **WHEN** se consulta GET /api/v1/fechas-academicas/{id}/html
- **THEN** se retorna HTML plano con tabla de fechas ordenadas por fecha ascendente

### Requirement: Aislamiento multi-tenant en fechas académicas
El sistema SHALL asegurar que un tenant solo acceda a sus propias fechas académicas.

#### Scenario: Fecha de otro tenant no visible
- **WHEN** se consulta una fecha académica de otro tenant
- **THEN** el sistema retorna 404

#### Scenario: Listado solo incluye fechas del tenant actual
- **WHEN** se listan fechas académicas
- **THEN** solo se incluyen fechas del tenant del usuario autenticado
