## ADDED Requirements

### Requirement: RBAC Pydantic Schemas
The system SHALL define Pydantic v2 schemas for Role and Permission management.

#### Scenario: Verify Role schema definition
- **WHEN** creating a Role
- **THEN** it must accept `name` and `description` (optional).

#### Scenario: Verify Permission schema definition
- **WHEN** creating a Permission
- **THEN** it must accept `name` (format: modulo:accion).
