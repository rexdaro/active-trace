# Spec: encryption-helper

## Overview
Provides utilities for encrypting and decrypting sensitive PII (Personally Identifiable Information) in the database.

## Requirements

### REQ-001: Data Encryption
The system MUST encrypt sensitive fields before storing them in the database.

**Scenarios:**

**Scenario: Encrypting PII**
- Given: A sensitive field (e.g., DNI) to store
- When: The encryption utility is applied
- Then: The stored data MUST be encrypted (cipher-text).

### REQ-002: Data Decryption
The system MUST decrypt sensitive fields when reading from the database.

**Scenarios:**

**Scenario: Decrypting PII**
- Given: Encrypted data stored in the database
- When: The data is read and the decryption utility is applied
- Then: The original plain-text MUST be recovered.
