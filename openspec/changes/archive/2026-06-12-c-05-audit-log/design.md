## Context

The system lacks a centralized mechanism to log user actions, making security auditing and troubleshooting difficult. We need an append-only audit log, specifically to track actions performed by administrators when impersonating other users.

## Goals / Non-Goals

**Goals:**
- Implement a centralized audit log.
- Capture relevant request details (user, action, timestamp, metadata).
- Specifically track impersonation context (original administrator ID).

**Non-Goals:**
- Full SIEM integration at this stage.
- Real-time alerting or dashboards.

## Decisions

- **Storage**: SQLAlchemy model `AuditLog` in `app/models/audit.py`.
- **Mechanism**: FastAPI Middleware (`app/middleware/audit.py`) to intercept requests and log them.
- **Impersonation**: Extend authentication context/security logic to include `impersonator_id` in the audit log entry if an active session is currently impersonating another user.

## Risks / Trade-offs

- **Performance**: Middleware adds overhead. Mitigation: Keep log entry creation asynchronous if possible or optimized.
- **Log Growth**: Audit logs will grow indefinitely. Mitigation: Establish a data retention/archival strategy (out of scope for this task, but noted for future).
