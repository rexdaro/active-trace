# Spec: jwt-auth

## Overview
Handles JWT token issuance, verification, and rotation.

## Requirements

### REQ-001: Token Issuance
The system MUST issue a JWT access token upon successful authentication.

**Scenarios:**

**Scenario: Successful login**
- Given: Valid user credentials
- When: Login request is processed
- Then: A JWT access token (15m expiry) and a refresh token are issued.

### REQ-002: Token Rotation
Refresh tokens MUST be rotated upon use to improve session security.

**Scenarios:**

**Scenario: Refreshing token**
- Given: A valid refresh token
- When: Refresh request is made
- Then: The old refresh token MUST be invalidated and a new pair issued.
