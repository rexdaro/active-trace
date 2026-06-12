## ADDED Requirements

### Requirement: RBAC FastAPI Dependency
The system SHALL provide a FastAPI dependency to enforce RBAC on endpoints.

#### Scenario: Verify RBAC dependency enforcement
- **WHEN** user requests an endpoint protected by RBAC
- **THEN** system MUST verify if the user has the required permission.
- **THEN** if not, return 403 Forbidden.
