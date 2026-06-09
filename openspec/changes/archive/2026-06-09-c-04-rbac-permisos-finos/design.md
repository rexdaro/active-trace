## Context

The current system lacks a formal authorization mechanism, hindering granular access control. We need to implement RBAC to support diverse user roles (ALUMNO, TUTOR, PROFESOR, etc.).

## Goals / Non-Goals

**Goals:**
- Implement RBAC models.
- Support fine-grained permission checks.
- Seed predefined roles.

**Non-Goals:**
- Complex attribute-based access control (ABAC) beyond simple role-based checks.

## Decisions

- **Database Structure**: Use standard junction table (RolePermission) to link roles and permissions.
- **Resolution**: Implement authorization guards at the application level to enforce role/permission requirements.

## Risks / Trade-offs

- [Risk] Performance impact of permission checks → Mitigation: Cache permission sets in the session.
