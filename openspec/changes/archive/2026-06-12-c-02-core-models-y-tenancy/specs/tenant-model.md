# Spec: tenant-model

## Overview
Defines the core Tenant structure and the mixin for tenant association in all domain models.

## Requirements

### REQ-001: Tenant Structure
The system MUST define a Tenant model with a unique identifier and essential metadata.

**Scenarios:**

**Scenario: Tenant creation**
- Given: A request to create a new tenant
- When: The tenant is saved
- Then: A unique UUID is assigned and metadata (created_at, updated_at) is populated.

### REQ-002: Tenant Association
The system MUST provide a mixin for models requiring tenant isolation.

**Scenarios:**

**Scenario: Model association**
- Given: A domain model requiring multi-tenancy
- When: The tenant-mixin is applied
- Then: The model MUST include a `tenant_id` field.
