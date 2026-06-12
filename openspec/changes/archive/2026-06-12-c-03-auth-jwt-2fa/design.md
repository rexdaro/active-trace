## Context

The application current authentication needs to be upgraded to support JWT-based authentication with refresh token rotation and 2FA, as specified in the proposal.

## Goals / Non-Goals

**Goals:**
- Implement JWT based auth.
- Refresh token rotation.
- 2FA.
- Maintain compatibility with FastAPI and Pydantic v2.

**Non-Goals:**
- OAuth2/OpenID Connect implementation (out of scope for this change).

## Decisions

- Use `python-jose` for JWT handling (chosen for its maturity).
- Use `argon2-cffi` for password hashing (security standard).
- Refresh token rotation: Store refresh token in a database and invalidate on use.

## Risks / Trade-offs

- [Complexity] Refresh token rotation increases DB hits → Use Redis if performance becomes an issue later.
- [UX] 2FA setup might be intrusive if not managed correctly → Provide simple UI/UX flow.
