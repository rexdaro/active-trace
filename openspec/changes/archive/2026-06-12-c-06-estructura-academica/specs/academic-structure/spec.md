## ADDED Requirements

### Requirement: Definición de Carrera
El sistema SHALL permitir definir una carrera académica.

#### Scenario: Creación de Carrera
- **WHEN** el administrador crea una carrera con nombre y código
- **THEN** la carrera debe quedar registrada en el sistema

### Requirement: Definición de Cohorte
El sistema SHALL permitir definir una cohorte para una carrera específica.

#### Scenario: Creación de Cohorte
- **WHEN** el administrador crea una cohorte asociada a una carrera
- **THEN** la cohorte debe estar vinculada a la carrera correspondiente

### Requirement: Definición de Materia
El sistema SHALL permitir definir materias para una cohorte.

#### Scenario: Creación de Materia
- **WHEN** el administrador crea una materia asociada a una cohorte
- **THEN** la materia debe estar vinculada a la cohorte correspondiente
