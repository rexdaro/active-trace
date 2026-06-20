# Design: RBAC with Fine-Grained Permissions

## Overview
The RBAC system will be designed to map Roles (e.g., `admin`, `editor`) to a set of fine-grained Permissions (e.g., `articles:create`, `articles:edit`, `users:list`).

## Architecture
- **SQLAlchemy 2.0 (async)**: Define M2M relationship between `Role` and `Permission`.
- **FastAPI Dependency**: A reusable `Depends(check_permission("modulo:accion"))` to protect endpoints.
- **Role Matrix**: A seedable YAML file defining the default permissions for each role.

## Schema
- `Role`: id, name
- `Permission`: id, name (modulo:accion)
- `RolePermission`: role_id, permission_id
