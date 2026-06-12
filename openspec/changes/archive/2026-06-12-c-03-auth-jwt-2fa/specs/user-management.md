# Spec: user-management

## Overview
Updates the User model to support 2FA and secure authentication status.

## Requirements

### REQ-001: User Model Update
The User model MUST be extended to store 2FA configuration data.

**Scenarios:**

**Scenario: User extension**
- Given: A User model
- When: 2FA implementation is performed
- Then: The model MUST include fields for 2FA secret and 2FA enabled status.
