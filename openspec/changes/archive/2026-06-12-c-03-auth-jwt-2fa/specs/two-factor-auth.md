# Spec: two-factor-auth

## Overview
Manages TOTP-based 2FA setup and verification for user accounts.

## Requirements

### REQ-001: 2FA Setup
Users SHOULD be able to enable and setup TOTP-based 2FA.

**Scenarios:**

**Scenario: Enabling 2FA**
- Given: An authenticated user
- When: User initiates 2FA setup
- Then: A secret key and QR code data MUST be provided for TOTP setup.

### REQ-002: 2FA Verification
The system MUST verify TOTP codes during authentication.

**Scenarios:**

**Scenario: 2FA Authentication**
- Given: A user with 2FA enabled
- When: User provides credentials and a valid TOTP code
- Then: Authentication MUST be successful and session established.
