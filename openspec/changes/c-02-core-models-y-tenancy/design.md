# Design: Multi-tenancy Implementation

## Context
The application is currently monolithic with no data isolation between clients. As we plan to scale to multiple tenants, we need to implement a mechanism to partition data.

## Goals / Non-Goals

**Goals:**
- Implement data isolation using `tenant_id` discriminator.
- Provide a secure and reusable pattern for repositories to enforce tenant isolation.
- Foundation for encrypting sensitive tenant data.

**Non-Goals:**
- Database-per-tenant architecture.
- Full security audit of all existing queries.

## Decisions

### 1. Multi-Tenancy Strategy: Discriminator Pattern
- **Decision**: Use a shared database with a `tenant_id` column on all tenant-specific tables.
- **Rationale**: Simplest to implement, allows easy data aggregation, avoids complexity of multiple databases/schemas.
- **Alternatives**: Database-per-tenant (complex), Schema-per-tenant (Postgres specific, complex migrations).

### 2. Isolation Enforcement
- **Decision**: Repository base class injects `tenant_id` filter.
- **Rationale**: Centralized enforcement point, reduces boilerplate in services.
- **Alternatives**: Global filter in SQLAlchemy (too magical, hard to debug).

## Risks / Trade-offs
- **[Risk] Tenant leakage**: Developers might forget to inject `tenant_id` in new queries.
  - **Mitigation**: Strict code reviews and integration tests using tenant-aware fixtures.
- **[Trade-off] Performance**: Extra `WHERE` clause on almost all queries.
  - **Mitigation**: Ensure `tenant_id` is indexed correctly on all partitioned tables.

## Migration Plan
1.  Introduce `Tenant` table.
2.  Add `tenant_id` column to existing tables (nullable initially).
3.  Backfill `tenant_id` for existing records (associated with a default tenant).
4.  Update repositories to inject `tenant_id`.
5.  Make `tenant_id` NOT NULL.
