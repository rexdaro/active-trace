# Tasks - c-05-audit-log

- [ ] Define SQLAlchemy `AuditLog` model in `app/models/audit.py`.
- [ ] Create and apply Alembic migration for the `audit_logs` table.
- [ ] Implement `AuditLogMiddleware` in `app/middleware/audit.py`.
- [ ] Register middleware in `app/main.py`.
- [ ] Update authentication service/security logic to track `impersonator_id` in audit entries.
- [ ] Implement tests for audit logging (including impersonation scenarios).
