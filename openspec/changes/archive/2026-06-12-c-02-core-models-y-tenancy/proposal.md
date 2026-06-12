# Proposal: c-02-core-models-y-tenancy

## Why
We need to implement multi-tenancy in our application to support secure isolation of data between different clients. This is critical for scaling to multiple customers while ensuring data sovereignty.

## What Changes
- **Implement `Tenant` model**: To define and identify clients.
- **Add multi-tenancy support to SQLAlchemy models**: Introduce a base class for models that require tenant isolation.
- **Implement repository base with tenant isolation**: Abstract tenant scoping in database operations.
- **Add encryption helper**: Security foundation for sensitive data.
- **Update Alembic migrations for tenant support**: Apply schema changes securely.

## Capabilities

### New Capabilities
- `tenant-model`: Core tenant structure and association logic.
- `tenant-isolation`: Repository level enforcement of tenant scoping.
- `encryption-helper`: Utility for secure handling of sensitive data.

### Modified Capabilities
- 

## Impact
- Core models: `tenant_id` introduction and dependency on base model class.
- Database access layer: All repositories need to be updated to support tenant scoping.
- Potential breaking change: Query patterns across the entire application will require tenant injection.
