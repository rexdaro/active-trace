## Why

The application requires secure authentication to protect user data and access. JWT authentication with refresh token rotation and 2FA will improve security by ensuring secure sessions and adding an extra layer of authentication.

## What Changes

- Implement JWT authentication system.
- Implement refresh token rotation.
- Implement 2FA (Two-Factor Authentication).
- Update User models to support 2FA.

## Capabilities

### New Capabilities
- `jwt-auth`: Handles JWT token issuance, verification, and rotation.
- `two-factor-auth`: Manages 2FA setup, verification, and backup codes.

### Modified Capabilities
- `user-management`: Updates user model to include 2FA status and secrets.

## Impact

- New API endpoints for auth (login, refresh, 2FA setup, 2FA verify).
- Updated user database schema.
- Dependencies: `python-jose`, `argon2-cffi`.
