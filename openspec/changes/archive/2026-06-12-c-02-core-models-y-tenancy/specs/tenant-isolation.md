# Spec: tenant-isolation

## Overview
Enforces row-level isolation by filtering all database queries by the current `tenant_id`.

## Requirements

### REQ-001: Automatic Scoping
The repository layer MUST automatically filter queries by the authenticated user's `tenant_id`.

**Scenarios:**

**Scenario: Querying isolated data**
- Given: A user authenticated in Tenant A
- When: Querying models with the tenant mixin
- Then: The database MUST only return rows where `tenant_id == TenantA_ID`.

### REQ-002: Cross-Tenant Protection
Queries without a tenant scope MUST be restricted or fail during review.

**Scenarios:**

**Scenario: Unscoped query**
- Given: An attempt to query models without providing a tenant context
- When: The query is executed
- Then: The repository MUST raise a security exception or require explicit tenant context.
