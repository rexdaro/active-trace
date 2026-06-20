# Spec: user-management

## Overview
User model was split across `User` (auth, `users` table) and `Usuario` (fiscal/PII, `usuarios` table). This change unifies both into a single `User` model on the `users` table.

## MODIFIED Requirements

### Requirement: User Model
The `User` model MUST contain all fields from both `users` and `usuarios` tables in a single entity.

**Fields:** id, tenant_id, email, hashed_password, is_2fa_enabled, totp_secret, dni (cifrado), cuil (cifrado), cbu (cifrado), nombre, datos_fiscales, datos_bancarios, regional, modalidad_cobro, created_at, updated_at, deleted_at.

#### Scenario: User has unified fields
- **WHEN** querying any user
- **THEN** all unified fields are available
- **AND** PII fields (dni, cuil, cbu) remain encrypted at rest

#### Scenario: Legacy Usuario table removed
- **WHEN** inspecting the database schema
- **THEN** the `usuarios` table no longer exists
- **AND** all its data has been migrated to `users`

### Requirement: Registration
The system SHALL allow a new user to register with email and password, automatically assigning the ALUMNO role.

#### Scenario: Public registration
- **WHEN** a new user sends POST /api/auth/register with email and password
- **THEN** the system creates a unified User
- **AND** assigns the ALUMNO role
- **AND** returns success

#### Scenario: Registration with existing email
- **WHEN** a user sends POST /api/auth/register with an existing email
- **THEN** the system returns HTTP 409 Conflict
