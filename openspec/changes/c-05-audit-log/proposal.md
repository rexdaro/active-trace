## Why

Implement an append-only Audit Log system to enhance system security, compliance, and debugging capabilities. This system will track user activities and specifically monitor actions performed during impersonation sessions.

## What Changes

- Add a new `AuditLog` database model and corresponding table.
- Implement a middleware for FastAPI to intercept requests and log relevant actions.
- Update the authentication service to track and flag actions performed by an administrator while impersonating a user.

## Capabilities

### New Capabilities
- `audit-log-service`: Middleware that intercepts requests and records actions in an immutable audit log.
- `impersonation-tracking`: Mechanism to link audit entries to the original administrator when acting as another user.

### Modified Capabilities
- `auth-service`: Extend to include session context for impersonation tracking.

## Impact

- Database schema modification (new table).
- Middleware addition in FastAPI application.
- Authentication service modification to support impersonation context.
