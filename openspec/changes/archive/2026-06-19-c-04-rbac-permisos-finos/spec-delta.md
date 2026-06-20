# Spec Delta: c-04-rbac-permisos-finos

## ADDED Requirements

### Requirement: RBAC Enforcement
WHEN a user accesses an endpoint protected by an RBAC dependency,
the system SHALL check if the user has the required permission for the module and action.

#### Scenario: Authorized Access
GIVEN a user with role "editor" that has permission "articles:edit"
WHEN the user attempts to "edit" an article
THEN the system allows the action.

#### Scenario: Unauthorized Access
GIVEN a user with role "viewer" that only has "articles:read"
WHEN the user attempts to "edit" an article
THEN the system denies the action with a 403 Forbidden response.
