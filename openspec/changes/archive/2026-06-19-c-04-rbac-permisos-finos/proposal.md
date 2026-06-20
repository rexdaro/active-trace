# Proposal: c-04-rbac-permisos-finos

## Why
The current system lacks granular access control, making it difficult to restrict actions based on user roles. We need a system that supports fine-grained permissions (format: `modulo:accion`) to ensure security and compliance.

## What Changes
1.  Introduction of a Role-Based Access Control (RBAC) system.
2.  Database schema updates to support Roles, Permissions, and their associations.
3.  Implementation of FastAPI dependencies to enforce RBAC on specific endpoints.
4.  Role seeding capability for initial system configuration.

## Impact
- **Database**: New tables (`roles`, `permissions`, `role_permissions`).
- **API**: New middleware/dependency decorators for FastAPI.
- **Initialization**: Migration or seeding script to populate default role-permission matrix.
