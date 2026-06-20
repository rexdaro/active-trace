# Spec: user-admin

## Overview
Admin capabilities for user management: creating users with any role, assigning and removing roles.

## ADDED Requirements

### Requirement: Admin creates user
The system SHALL allow an admin to create a new user with email, password, and any role.

#### Scenario: Admin creates user with role
- **WHEN** an admin sends POST /api/v1/usuarios with email, password, and role_id
- **THEN** the system creates the user
- **AND** assigns the specified role
- **AND** returns the created user with HTTP 201

#### Scenario: Admin creates user without role
- **WHEN** an admin sends POST /api/v1/usuarios with email and password (no role)
- **THEN** the system creates the user
- **AND** assigns role ALUMNO by default
- **AND** returns the created user with HTTP 201

#### Scenario: Duplicate email rejected
- **WHEN** an admin sends POST /api/v1/usuarios with an existing email
- **THEN** the system returns HTTP 409 Conflict
- **AND** does not create the user

### Requirement: Admin assigns role
The system SHALL allow an admin to assign a role to an existing user.

#### Scenario: Assign existing role
- **WHEN** an admin sends POST /api/v1/usuarios/{id}/roles with role_name
- **THEN** the system assigns the role to the user
- **AND** returns success

#### Scenario: Assign non-existent role
- **WHEN** an admin sends POST /api/v1/usuarios/{id}/roles with invalid role_name
- **THEN** the system returns HTTP 404

#### Scenario: Assign duplicate role
- **WHEN** an admin sends POST /api/v1/usuarios/{id}/roles with a role the user already has
- **THEN** the system returns success with a message indicating the role was already assigned
