## ADDED Requirements

### Requirement: RBAC Database Models
The system SHALL define SQLAlchemy 2.0 models for Role, Permission, and the many-to-many relationship RolePermission and UserRole.

#### Scenario: Verify Role model definition
- **WHEN** inspecting the database schema
- **THEN** it must contain a `roles` table with `id`, `name`, and `description` columns.

#### Scenario: Verify Permission model definition
- **WHEN** inspecting the database schema
- **THEN** it must contain a `permissions` table with `id` and `name` (format: modulo:accion) columns.

#### Scenario: Verify RolePermission association
- **WHEN** inspecting the database schema
- **THEN** it must contain a `role_permissions` table linking `role_id` and `permission_id`.

#### Scenario: Verify UserRole association
- **WHEN** inspecting the database schema
- **THEN** it must contain a `user_roles` table linking `user_id` and `role_id`.
